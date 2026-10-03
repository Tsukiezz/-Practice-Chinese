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
from sepay_gateway import checkout_fields, process_ipn


class GatewayTest(unittest.TestCase):
    def setUp(self):
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

    def test_checkout_route_and_browser_return_do_not_grant_premium(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from sepay_gateway import register_gateway
        app = FastAPI()
        register_gateway(app)
        with TestClient(app) as client:
            response = client.get(self.order['payment_url'].replace('https://example.test', ''))
            self.assertEqual(response.status_code, 200)
            self.assertIn('https://pay.sepay.vn/v1/checkout/init', response.text)
            self.assertNotIn('test-only-secret', response.text)
            self.assertEqual(response.headers['cache-control'], 'no-store')
            client.get('/payment/sepay/return', params={'code': self.order['order_code'], 'result': 'success'})
            with storage.database() as c:
                self.assertEqual(c.execute('SELECT premium_until FROM users WHERE id=?', (self.uid,)).fetchone()[0], 0)
            self.assertEqual(client.post('/api/payment/sepay-ipn', json=self.payload).status_code, 401)
            self.assertEqual(client.post('/api/payment/sepay-ipn', json=self.payload,
                headers={'X-Secret-Key': 'test-only-secret'}).status_code, 200)
