import copy
import os
from pathlib import Path
import sqlite3
import uuid
import time
import unittest
from unittest.mock import patch

from fastapi import HTTPException
import database as storage
from premium_service import create_premium_order, cleanup_expired_pending_orders, process_sepay_webhook
from sepay_gateway import checkout_fields, process_ipn, reconcile_order, _checks
import httpx


class GatewayTest(unittest.TestCase):
    def setUp(self):
        _checks.clear()
        self.api = patch('sepay_gateway.httpx.Client')
        self.api_client = self.api.start().return_value.__enter__.return_value
        self.api_client.get.side_effect = httpx.ConnectError('offline test')
        self.addCleanup(self.api.stop)
        self.previous = storage.DB_PATH
        uri = 'file:payment-' + uuid.uuid4().hex + '?mode=memory&cache=shared'
        original_connect = sqlite3.connect
        self.keeper = original_connect(uri, uri=True)
        self.connector = patch('database.sqlite3.connect', side_effect=lambda *args, **kwargs: original_connect(uri, uri=True))
        self.connector.start()
        self.env = patch.dict(os.environ, {'SEPAY_MERCHANT_ID': 'SP-TEST-SAMPLE',
            'SEPAY_SECRET_KEY': 'test-only-secret', 'SEPAY_PUBLIC_URL': 'https://example.test',
            'TURSO_DATABASE_URL': '', 'HANZIGO_DB_DRIVER': 'sqlite'})
        self.env.start()
        storage.init_db()
        with storage.database() as c:
            self.uid = c.execute("INSERT INTO users(name,email,password_hash,salt,role,created_at) VALUES('Test','test@example.test','hash','salt','student',?)", (int(time.time()),)).lastrowid
            self.order = create_premium_order(c, self.uid, '1_month')
        self.payload = {'notification_type': 'ORDER_PAID',
            'order': {'id': 'sepay-order', 'order_invoice_number': self.order['order_code'],
                      'order_status': 'CAPTURED', 'order_currency': 'VND', 'order_amount': '49000.00'},
            'transaction': {'id': 'tx-unique', 'transaction_status': 'APPROVED',
                            'transaction_type': 'PAYMENT', 'transaction_currency': 'VND', 'transaction_amount': '49000'}}

    def tearDown(self):
        self.env.stop()
        storage.DB_PATH = self.previous
        self.connector.stop()
        self.keeper.close()

    def notify(self, payload=None, secret='test-only-secret'):
        with storage.database() as c:
            c.execute('BEGIN IMMEDIATE')
            return process_ipn(c, payload or self.payload, secret)

    def test_authenticated_payment_is_idempotent_and_late_payment_retained(self):
        with storage.database() as c:
            c.execute('UPDATE premium_orders SET created_at=?', (int(time.time()) - 2000,))
            cleanup_expired_pending_orders(c)
            self.assertIsNotNone(c.execute('SELECT id FROM premium_orders').fetchone())
        self.notify()
        with storage.database() as c:
            before = dict(c.execute('SELECT premium_until,streak_freezes FROM users WHERE id=?', (self.uid,)).fetchone())
        self.notify()
        with storage.database() as c:
            self.assertEqual(dict(c.execute('SELECT premium_until,streak_freezes FROM users WHERE id=?', (self.uid,)).fetchone()), before)
        self.assertEqual(before['streak_freezes'], 3)
        self.assertGreater(before['premium_until'], int(time.time()))

    def test_rejects_missing_auth_wrong_amount_currency_and_failed_payment(self):
        for secret in ['', 'wrong-secret']:
            with self.assertRaises(HTTPException) as raised:
                self.notify(secret=secret)
            self.assertEqual(raised.exception.status_code, 401)
        for group, key, value in [('order', 'order_amount', '1'), ('transaction', 'transaction_amount', 'NaN'),
                                   ('order', 'order_currency', 'USD'), ('transaction', 'transaction_status', 'FAILED')]:
            p = copy.deepcopy(self.payload)
            p[group][key] = value
            with self.assertRaises(HTTPException):
                self.notify(p)
        with storage.database() as c:
            self.assertEqual(c.execute('SELECT premium_until FROM users WHERE id=?', (self.uid,)).fetchone()[0], 0)

    def test_transaction_cannot_pay_two_orders(self):
        self.notify()
        with storage.database() as c:
            second = create_premium_order(c, self.uid, '1_month')
        p = copy.deepcopy(self.payload)
        p['order']['order_invoice_number'] = second['order_code']
        with self.assertRaises(HTTPException) as raised:
            self.notify(p)
        self.assertEqual(raised.exception.status_code, 409)

    def test_checkout_matches_official_sdk_signature(self):
        fields = checkout_fields(self.order)
        import base64, hashlib, hmac
        message = ','.join(f'{key}={value}' for key, value in fields.items() if key != 'signature')
        self.assertEqual(fields['signature'], base64.b64encode(hmac.new(b'test-only-secret', message.encode(), hashlib.sha256).digest()).decode())
        self.assertNotIn('test-only-secret', str(fields))
        self.assertIn('/payment/sepay/checkout?', self.order['payment_url'])

    def test_bank_webhook_fails_closed_without_credentials(self):
        with storage.database() as c:
            c.execute("UPDATE sepay_config SET api_key='' WHERE id=1")
            with self.assertRaises(HTTPException) as raised:
                process_sepay_webhook(c, {'content': self.order['order_code'], 'transferAmount': 49000})
        self.assertEqual(raised.exception.status_code, 401)

    def test_bank_transfer_can_complete_gateway_order_once(self):
        for plan, amount, days in [('1_month', 49000, 30), ('1_year', 490000, 365)]:
            with self.subTest(plan=plan), storage.database() as c:
                c.execute("UPDATE sepay_config SET api_key='bank-secret' WHERE id=1")
                c.execute('UPDATE users SET premium_until=0, streak_freezes=0 WHERE id=?', (self.uid,))
                order = create_premium_order(c, self.uid, plan)
                payload = {'id': 'bank-' + plan, 'code': order['order_code'],
                           'transferType': 'in', 'transferAmount': amount, 'accountNumber': '80001795444'}
                before = int(time.time())
                result = process_sepay_webhook(c, payload, auth_header='Apikey bank-secret')
                self.assertTrue(result['success'])
                self.assertAlmostEqual(result['premium_until'], before + days * 86400, delta=2)
                process_sepay_webhook(c, payload, auth_header='Apikey bank-secret')
                self.assertEqual(c.execute('SELECT premium_until FROM users WHERE id=?', (self.uid,)).fetchone()[0], result['premium_until'])

    def mock_remote_order(self, detail):
        self.api_client.get.side_effect = [
            httpx.Response(200, json={'data': detail}, request=httpx.Request('GET', 'https://pgapi.sepay.vn/v1/order/detail/remote-order'))]

    def test_reconcile_missed_ipn_and_repeat(self):
        detail = dict(self.payload['order'], transactions=[self.payload['transaction']])
        self.mock_remote_order(detail)
        reconcile_order(self.order['order_code'], self.uid)
        with storage.database() as c:
            until = c.execute('SELECT premium_until FROM users WHERE id=?', (self.uid,)).fetchone()[0]
            self.assertAlmostEqual(until, int(time.time()) + 30 * 86400, delta=2)
        reconcile_order(self.order['order_code'], self.uid)
        self.assertEqual(self.api_client.get.call_count, 1)
        self.assertTrue(self.api_client.get.call_args.args[0].endswith('/' + self.order['order_code']))
        self.notify()
        with storage.database() as c:
            self.assertEqual(c.execute('SELECT premium_until FROM users WHERE id=?', (self.uid,)).fetchone()[0], until)

    def test_reconcile_rejects_wrong_amount_and_owner(self):
        reconcile_order(self.order['order_code'], self.uid + 999)
        self.api_client.get.assert_not_called()
        detail = dict(self.payload['order'], order_amount='1', transactions=[self.payload['transaction']])
        self.mock_remote_order(detail)
        reconcile_order(self.order['order_code'], self.uid)
        with storage.database() as c:
            self.assertEqual(c.execute('SELECT premium_until FROM users WHERE id=?', (self.uid,)).fetchone()[0], 0)

    def test_captured_bank_order_without_transactions_is_reconciled(self):
        self.mock_remote_order(dict(self.payload['order'], transactions=[]))
        reconcile_order(self.order['order_code'], self.uid)
        with storage.database() as c:
            row = c.execute('SELECT * FROM premium_orders WHERE order_code=?', (self.order['order_code'],)).fetchone()
            self.assertEqual(row['status'], 'completed')
            self.assertEqual(row['sepay_reference_code'], 'sepay-order')
        self.notify()
        with storage.database() as c:
            self.assertEqual(c.execute('SELECT streak_freezes FROM users WHERE id=?', (self.uid,)).fetchone()[0], 3)

    def test_api_evidence_must_match_invoice_currency_status_and_identity(self):
        for key, value in [('order_invoice_number', 'HZG999999'), ('order_status', 'CANCELLED'),
                           ('order_currency', 'USD'), ('order_amount', 'NaN'), ('id', '')]:
            _checks.clear()
            self.mock_remote_order(dict(self.payload['order'], **{key: value}))
            reconcile_order(self.order['order_code'], self.uid)
            with storage.database() as c:
                self.assertEqual(c.execute('SELECT premium_until FROM users WHERE id=?', (self.uid,)).fetchone()[0], 0)

    def test_polling_retries_after_five_seconds(self):
        with patch('sepay_gateway.time.monotonic', side_effect=[100, 104, 105]):
            for _ in range(3):
                reconcile_order(self.order['order_code'], self.uid)
        self.assertEqual(self.api_client.get.call_count, 2)

    def test_reconcile_yearly_late_payment_extends_existing_membership(self):
        base = int(time.time()) + 10 * 86400
        with storage.database() as c:
            order = create_premium_order(c, self.uid, '1_year')
            c.execute('UPDATE users SET premium_until=? WHERE id=?', (base, self.uid))
            c.execute("UPDATE premium_orders SET status='cancelled' WHERE order_code=?", (order['order_code'],))
        transaction = dict(self.payload['transaction'], transaction_amount='490000')
        detail = dict(self.payload['order'], order_invoice_number=order['order_code'],
                      order_amount='490000.00', transactions=[transaction])
        self.mock_remote_order(detail)
        reconcile_order(order['order_code'], self.uid)
        with storage.database() as c:
            self.assertEqual(c.execute('SELECT premium_until FROM users WHERE id=?', (self.uid,)).fetchone()[0], base + 365 * 86400)

    def test_bank_transfer_rejects_wrong_account_missing_direction_and_underpayment(self):
        with storage.database() as c:
            c.execute("UPDATE sepay_config SET api_key='bank-secret' WHERE id=1")
            good = {'id': 'bank-test', 'code': self.order['order_code'], 'transferType': 'in',
                    'transferAmount': 49000, 'accountNumber': '80001795444'}
            for key, value in [('accountNumber', 'other-account'), ('transferType', ''), ('transferAmount', 100)]:
                process_sepay_webhook(c, dict(good, **{key: value}), auth_header='Apikey bank-secret')
            self.assertEqual(c.execute('SELECT premium_until FROM users WHERE id=?', (self.uid,)).fetchone()[0], 0)

    def test_gateway_ipn_can_arrive_at_legacy_webhook_url(self):
        from main import app
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            self.assertEqual(client.post('/api/payment/sepay-webhook', json=self.payload).status_code, 401)
            self.assertEqual(client.post('/api/payment/sepay-webhook', json=self.payload,
                                        headers={'X-Secret-Key': 'test-only-secret'}).status_code, 200)

    def test_provider_outage_does_not_grant_premium_and_is_throttled(self):
        reconcile_order(self.order['order_code'], self.uid)
        reconcile_order(self.order['order_code'], self.uid)
        self.assertEqual(self.api_client.get.call_count, 1)
        with storage.database() as c:
            self.assertEqual(c.execute('SELECT premium_until FROM users WHERE id=?', (self.uid,)).fetchone()[0], 0)

    def test_checkout_route_and_browser_return_do_not_grant_premium(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from sepay_gateway import register_gateway
        app = FastAPI()
        register_gateway(app)
        with TestClient(app) as client:
            response = client.get(self.order['payment_url'].replace('https://example.test', ''))
            self.assertEqual(response.status_code, 200)
            status_url = self.order['payment_url'].replace('https://example.test', '').replace('/payment/sepay/checkout?', '/api/payment/sepay-status?')
            self.assertFalse(client.get(status_url).json()['is_completed'])
            self.assertEqual(client.get(status_url + 'bad').status_code, 403)

            self.assertIn('https://pay.sepay.vn/v1/checkout/init', response.text)
            self.assertNotIn('test-only-secret', response.text)
            self.assertEqual(response.headers['cache-control'], 'no-store')
            client.get('/payment/sepay/return', params={'code': self.order['order_code'], 'result': 'success'})
            with storage.database() as c:
                self.assertEqual(c.execute('SELECT premium_until FROM users WHERE id=?', (self.uid,)).fetchone()[0], 0)
            self.assertEqual(client.post('/api/payment/sepay-ipn', json=self.payload).status_code, 401)
            self.assertEqual(client.post('/api/payment/sepay-ipn', json=self.payload,
                headers={'X-Secret-Key': 'test-only-secret'}).status_code, 200)

            self.assertTrue(client.get(status_url).json()['is_completed'])
