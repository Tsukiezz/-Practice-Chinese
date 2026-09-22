"""Test OTP registration and forgot-password flows."""
import json
import sqlite3
import unittest
from fastapi.testclient import TestClient

from database import database, init_db
from main import app


class TestAuthOtp(unittest.TestCase):
    def _cleanup(self):
        with database() as conn:
            user = conn.execute("SELECT id FROM users WHERE email=?", (self.test_email,)).fetchone()
            if user:
                conn.execute("DELETE FROM sessions WHERE user_id=?", (user["id"],))
                conn.execute("DELETE FROM users WHERE id=?", (user["id"],))
            conn.execute("DELETE FROM verification_codes WHERE email=?", (self.test_email,))

    def setUp(self):
        init_db()
        self.client = TestClient(app)
        self.test_email = "tester_otp@example.com"
        self._cleanup()

    def tearDown(self):
        self._cleanup()

    def test_register_request_and_verify(self):
        # 1. Request registration
        req = self.client.post("/api/auth/register-request", json={
            "name": "Người Dùng Mới",
            "email": self.test_email,
            "password": "Password123@"
        })
        self.assertEqual(req.status_code, 200)
        self.assertEqual(req.json()["status"], "ok")

        # Check that code exists in DB
        with database() as conn:
            row = conn.execute(
                "SELECT * FROM verification_codes WHERE email=? AND purpose='register' AND used=0",
                (self.test_email,)
            ).fetchone()
            self.assertIsNotNone(row)
            code = row["code"]

        # 2. Test verify with wrong code
        fail_res = self.client.post("/api/auth/register-verify", json={
            "email": self.test_email,
            "code": "000000"
        })
        self.assertEqual(fail_res.status_code, 400)

        # 3. Test verify with correct code
        ok_res = self.client.post("/api/auth/register-verify", json={
            "email": self.test_email,
            "code": code
        })
        self.assertEqual(ok_res.status_code, 201)
        data = ok_res.json()
        self.assertIn("token", data)
        self.assertEqual(data["user"]["email"], self.test_email)
        self.assertEqual(data["user"]["role"], "student")

        # 4. Request registration again with same email -> 409
        dup_res = self.client.post("/api/auth/register-request", json={
            "name": "Người Dùng Mới 2",
            "email": self.test_email,
            "password": "Password123@"
        })
        self.assertEqual(dup_res.status_code, 409)

    def test_forgot_password_request_and_verify(self):
        # Create user first via register-request & verify
        self.client.post("/api/auth/register-request", json={
            "name": "Tester Quên MK",
            "email": self.test_email,
            "password": "OldPassword123"
        })
        with database() as conn:
            reg_code = conn.execute(
                "SELECT code FROM verification_codes WHERE email=? AND purpose='register' AND used=0",
                (self.test_email,)
            ).fetchone()["code"]
        self.client.post("/api/auth/register-verify", json={
            "email": self.test_email,
            "code": reg_code
        })

        # 1. Request forgot password
        forgot_res = self.client.post("/api/auth/forgot-password-request", json={
            "email": self.test_email
        })
        self.assertEqual(forgot_res.status_code, 200)

        with database() as conn:
            reset_row = conn.execute(
                "SELECT code FROM verification_codes WHERE email=? AND purpose='forgot_password' AND used=0",
                (self.test_email,)
            ).fetchone()
            self.assertIsNotNone(reset_row)
            reset_code = reset_row["code"]

        # 2. Reset password with wrong code
        bad_reset = self.client.post("/api/auth/forgot-password-verify", json={
            "email": self.test_email,
            "code": "999999",
            "new_password": "NewStrongPassword456"
        })
        self.assertEqual(bad_reset.status_code, 400)

        # 3. Reset password with correct code
        good_reset = self.client.post("/api/auth/forgot-password-verify", json={
            "email": self.test_email,
            "code": reset_code,
            "new_password": "NewStrongPassword456"
        })
        self.assertEqual(good_reset.status_code, 200)

        # 4. Verify login with old password fails
        old_login = self.client.post("/api/auth/login", json={
            "email": self.test_email,
            "password": "OldPassword123"
        })
        self.assertEqual(old_login.status_code, 401)

        # 5. Verify login with new password succeeds
        new_login = self.client.post("/api/auth/login", json={
            "email": self.test_email,
            "password": "NewStrongPassword456"
        })
        self.assertEqual(new_login.status_code, 200)
        self.assertIn("token", new_login.json())


if __name__ == "__main__":
    unittest.main()
