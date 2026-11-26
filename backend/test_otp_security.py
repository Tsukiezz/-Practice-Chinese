"""OTP abuse, storage and transaction checks on a disposable database."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette.requests import Request
import database as storage
import otp_security as otp
from main import app
from usecase_features import init_features


class OTPProtectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_path = storage.DB_PATH
        storage.DB_PATH = Path(self.temp.name) / 'otp.db'
        storage.init_db()
        init_features()
        self.client = TestClient(app)
        self.email = 'otp-owner@example.test'
        self.sent = []
        self.delivery = patch('main.send_verification_email', side_effect=self.capture)
        self.delivery.start()
        self.addCleanup(self.delivery.stop)
        self.request = Request({'type':'http', 'headers':[], 'client':('192.0.2.1', 123)})

    def tearDown(self):
        storage.DB_PATH = self.old_path
        self.temp.cleanup()

    def capture(self, email, code, purpose):
        self.sent.append((email, code, purpose))
        return True

    def register(self):
        response = self.client.post('/api/auth/register', json={
            'name':'OTP Owner', 'email':self.email, 'password':'Original-password-123'})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()['token']

    def send_reset(self):
        return self.client.post('/api/auth/forgot-password-request', json={'email':self.email})

    def verify(self, code, legacy=False):
        body = {'email':self.email, 'code':code,
                'password' if legacy else 'new_password':'Replacement-password-456'}
        return self.client.post('/api/auth/recovery/confirm' if legacy else '/api/auth/forgot-password-verify', json=body)

    def test_hash_is_salted_bound_to_identity_and_purpose(self):
        value = otp.encode_code(self.email, 'register', '123456')
        self.assertTrue(otp.matches_code(self.email, 'register', '123456', value))
        self.assertFalse(otp.matches_code(self.email, 'forgot_password', '123456', value))
        self.assertFalse(otp.matches_code('other@example.test', 'register', '123456', value))
        self.assertNotEqual(value, otp.encode_code(self.email, 'register', '123456'))
        self.assertNotIn('123456', value)

    def test_send_cooldown_is_shared_by_recovery_alias(self):
        self.register()
        self.assertEqual(self.send_reset().status_code, 200)
        with patch('usecase_features.smtp_ready', return_value=True):
            blocked = self.client.post('/api/auth/recovery', json={'email':self.email})
        self.assertEqual(blocked.status_code, 429)
        self.assertEqual(blocked.headers['retry-after'], '60')
        self.assertEqual(len(self.sent), 1)

    def test_five_wrong_attempts_persist_across_both_verify_routes(self):
        self.register()
        self.assertEqual(self.send_reset().status_code, 200)
        code = self.sent[-1][1]
        wrong = '000000' if code != '000000' else '999999'
        for i in range(5):
            self.assertEqual(self.verify(wrong, legacy=bool(i % 2)).status_code, 400)
        self.assertEqual(self.verify(code).status_code, 400)
        with storage.database() as conn:
            row = conn.execute('SELECT attempts,used FROM verification_codes').fetchone()
        self.assertEqual((row['attempts'],row['used']), (5,1))

    def test_success_revokes_sessions_consumes_once_and_clears_temporary_data(self):
        token = self.register()
        self.assertEqual(self.send_reset().status_code, 200)
        code = self.sent[-1][1]
        self.assertEqual(self.verify(code, legacy=True).status_code, 204)
        self.assertEqual(self.verify(code).status_code, 400)
        self.assertEqual(self.client.get('/api/me', headers={'Authorization':'Bearer '+token}).status_code, 401)
        with storage.database() as conn:
            row = conn.execute('SELECT code,used,temp_data_json FROM verification_codes').fetchone()
        self.assertTrue(row['code'].startswith('h1$'))
        self.assertEqual(row['used'], 1)
        self.assertEqual(row['temp_data_json'], '{}')

    def test_expiry_and_exact_six_ascii_digits(self):
        self.register()
        self.send_reset()
        code = self.sent[-1][1]
        with patch('otp_security.now', return_value=otp.now()+601):
            self.assertEqual(self.verify(code).status_code, 400)
        for invalid in ('1234','1234567','abcdef','１２３４５６'):
            self.assertEqual(self.verify(invalid).status_code, 422)

    def test_unknown_and_locked_accounts_have_same_response_without_sending(self):
        unknown = self.send_reset()
        self.register()
        with storage.database() as conn:
            conn.execute('UPDATE users SET is_active=0 WHERE email=?', (self.email,))
            conn.execute("DELETE FROM request_limits WHERE key LIKE 'otp:%'")
        locked = self.send_reset()
        self.assertEqual(unknown.status_code, 200)
        self.assertEqual(unknown.json(), locked.json())
        self.assertEqual(self.sent, [])

    def test_existing_otp_cannot_reset_a_locked_account(self):
        self.register()
        self.send_reset()
        with storage.database() as conn:
            conn.execute('UPDATE users SET is_active=0 WHERE email=?', (self.email,))
        self.assertEqual(self.verify(self.sent[-1][1]).status_code, 400)

    def test_password_change_invalidates_earlier_reset_code(self):
        token = self.register()
        self.send_reset()
        result = self.client.post('/api/account/password', headers={'Authorization':'Bearer '+token},
            json={'old_password':'Original-password-123','new_password':'Changed-password-789'})
        self.assertEqual(result.status_code, 204)
        self.assertEqual(self.verify(self.sent[-1][1]).status_code, 400)

    def test_email_hourly_limit_cannot_be_bypassed_by_resend_or_purpose(self):
        stamp = otp.now()
        for i in range(5):
            with patch('otp_security.now', return_value=stamp+i*61):
                otp.limit_send(self.email, 'register' if i%2 else 'forgot_password', self.request)
        with patch('otp_security.now', return_value=stamp+5*61):
            with self.assertRaises(HTTPException) as error:
                otp.limit_send(self.email, 'register', self.request)
        self.assertEqual(error.exception.status_code, 429)

    def test_ip_rate_limit_ignores_untrusted_forwarded_headers(self):
        stamp = otp.now()
        for i in range(10):
            spoof = Request({'type':'http','headers':[(b'x-forwarded-for',f'192.0.2.{i+10}'.encode())],
                             'client':('192.0.2.1',123)})
            with patch('otp_security.now', return_value=stamp):
                otp.limit_send(f'user{i}@example.test', 'register', spoof)
        with patch('otp_security.now', return_value=stamp):
            with self.assertRaises(HTTPException) as error:
                otp.limit_send('overflow@example.test', 'register', self.request)
        self.assertEqual(error.exception.status_code, 429)
        self.assertEqual(otp.client_ip(spoof), '192.0.2.1')
        with patch.dict(os.environ, {'VERCEL':'1'}):
            trusted = Request({'type':'http','headers':[(b'x-vercel-forwarded-for',b'203.0.113.8')],
                               'client':('127.0.0.1',123)})
            self.assertEqual(otp.client_ip(trusted), '203.0.113.8')

    def test_concurrent_delivery_reservations_allow_only_one(self):
        def reserve(_):
            try:
                otp.limit_send(self.email, 'register', self.request)
                return 200
            except HTTPException as error:
                return error.status_code
        with ThreadPoolExecutor(max_workers=5) as pool:
            statuses = list(pool.map(reserve, range(5)))
        self.assertEqual(sorted(statuses), [200,429,429,429,429])

    def test_concurrent_consumption_is_single_use(self):
        with storage.database() as conn:
            row_id, code = otp.create_code(conn, self.email, 'register', {'test':True})
        otp.deliver_code(row_id, self.email, 'register', code, self.capture)
        consumed = []
        def verify(_):
            try:
                otp.consume_code(self.email, 'register', code, self.request,
                    lambda conn,row: consumed.append(row['id']) or True)
                return 200
            except HTTPException as error:
                return error.status_code
        with ThreadPoolExecutor(max_workers=4) as pool:
            statuses = list(pool.map(verify, range(4)))
        self.assertEqual(sorted(statuses), [200,400,400,400])
        self.assertEqual(consumed, [row_id])

    def test_migration_is_idempotent_and_preserves_unexpired_code(self):
        with storage.database() as conn:
            conn.execute('''INSERT INTO verification_codes(email,code,purpose,expires_at,created_at)
                VALUES(?, '123456', 'register', ?, ?)''', (self.email, otp.now()+600, otp.now()))
            storage.init_auth_tables(conn)
            first = conn.execute('SELECT code FROM verification_codes').fetchone()[0]
            storage.init_auth_tables(conn)
            second = conn.execute('SELECT code FROM verification_codes').fetchone()[0]
        self.assertEqual(first, second)
        self.assertTrue(otp.matches_code(self.email, 'register', '123456', first))

    def test_failed_account_mutation_rolls_back_code_consumption(self):
        with storage.database() as conn:
            row_id, code = otp.create_code(conn, self.email, 'register', {'test':True})
        otp.deliver_code(row_id, self.email, 'register', code, self.capture)
        def broken_mutation(conn, row):
            conn.execute("UPDATE verification_codes SET temp_data_json='{}' WHERE id=?", (row['id'],))
            raise RuntimeError('transaction failed')
        with self.assertRaises(RuntimeError):
            otp.consume_code(self.email, 'register', code, self.request, broken_mutation)
        self.assertTrue(otp.consume_code(self.email, 'register', code, self.request, lambda conn,row: True))

    def test_verification_flood_limit_is_shared_without_a_valid_code(self):
        for i in range(20):
            self.assertEqual(self.verify('123456', legacy=bool(i%2)).status_code, 400)
        blocked = self.verify('123456')
        self.assertEqual(blocked.status_code, 429)
        self.assertIn('retry-after', blocked.headers)

    def test_production_missing_server_secret_fails_closed(self):
        with patch.dict(os.environ, {'VERCEL':'1', 'OTP_HASH_SECRET':''}), patch('main.smtp_is_configured', return_value=True):
            self.assertEqual(self.send_reset().status_code, 503)
        self.assertEqual(self.sent, [])

    def test_inflight_old_delivery_cannot_reactivate_after_consumption(self):
        with storage.database() as conn:
            old_id, old = otp.create_code(conn, self.email, 'register', {'test':True})
            new_id, new = otp.create_code(conn, self.email, 'register', {'test':True})
        otp.deliver_code(new_id, self.email, 'register', new, self.capture)
        otp.consume_code(self.email, 'register', new, self.request, lambda conn,row: True)
        otp.deliver_code(old_id, self.email, 'register', old, self.capture)
        with self.assertRaises(HTTPException):
            otp.consume_code(self.email, 'register', old, self.request, lambda conn,row: True)
