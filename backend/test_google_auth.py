"""Unit tests for Google Sign-In with customizable learner display name."""
import unittest
from fastapi.testclient import TestClient

from database import database, init_db
from main import app


class TestGoogleAuth(unittest.TestCase):
    def setUp(self):
        init_db()
        self.client = TestClient(app)
        self._clean()

    def tearDown(self):
        self._clean()

    def _clean(self):
        with database() as conn:
            conn.execute("DELETE FROM profiles WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%@google-test.test')")
            conn.execute("DELETE FROM sessions WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%@google-test.test')")
            conn.execute("DELETE FROM users WHERE email LIKE '%@google-test.test'")

    def test_google_config_endpoint(self):
        res = self.client.get("/api/auth/google-config")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("client_id", data)
        self.assertIn("is_configured", data)

    def test_google_login_new_user_with_custom_chosen_name(self):
        # Khách đăng nhập bằng Google và tự do chọn tên hiển thị của mình
        payload = {
            "email": "learner1@google-test.test",
            "name": "Tiểu Long Nữ",
            "avatar": "https://lh3.googleusercontent.com/test-avatar",
        }
        res = self.client.post("/api/auth/google-login", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("token", data)
        self.assertEqual(data["user"]["name"], "Tiểu Long Nữ")
        self.assertEqual(data["user"]["email"], "learner1@google-test.test")
        self.assertEqual(data["user"]["role"], "student")
        self.assertEqual(data["user"]["avatar"], "https://lh3.googleusercontent.com/test-avatar")

        # Verify session token works with authenticated endpoints
        session_res = self.client.get("/api/auth/student-session", headers={"Authorization": f"Bearer {data['token']}"})
        self.assertEqual(session_res.status_code, 200)
        self.assertEqual(session_res.json()["name"], "Tiểu Long Nữ")

    def test_google_login_existing_user_updates_chosen_name(self):
        # Lần 1: đăng nhập với tên "Bảo Nam"
        res1 = self.client.post("/api/auth/google-login", json={
            "email": "learner2@google-test.test",
            "name": "Bảo Nam",
        })
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1.json()["user"]["name"], "Bảo Nam")

        # Lần 2: khách đăng nhập lại và đổi tên thành "Minh Thư HSK6"
        res2 = self.client.post("/api/auth/google-login", json={
            "email": "learner2@google-test.test",
            "name": "Minh Thư HSK6",
        })
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json()["user"]["name"], "Minh Thư HSK6")

    def test_google_login_empty_name_or_invalid_email_rejected(self):
        # Empty name
        res_no_name = self.client.post("/api/auth/google-login", json={
            "email": "learner3@google-test.test",
            "name": "   ",
        })
        self.assertEqual(res_no_name.status_code, 422)

        # Invalid email
        res_bad_email = self.client.post("/api/auth/google-login", json={
            "email": "not-an-email",
            "name": "Alex",
        })
        self.assertEqual(res_bad_email.status_code, 422)

    def test_google_login_locked_user_forbidden(self):
        # Create user then lock
        res = self.client.post("/api/auth/google-login", json={
            "email": "locked@google-test.test",
            "name": "Locked User",
        })
        uid = res.json()["user"]["id"]
        with database() as conn:
            conn.execute("UPDATE users SET is_active=0 WHERE id=?", (uid,))

        res_locked = self.client.post("/api/auth/google-login", json={
            "email": "locked@google-test.test",
            "name": "Locked User",
        })
        self.assertEqual(res_locked.status_code, 403)

    def test_google_login_with_access_token(self):
        # Đăng nhập với Google Access Token hợp lệ
        res = self.client.post("/api/auth/google-login", json={
            "email": "tokenuser@google-test.test",
            "name": "Học Viên Token",
            "access_token": "test_access_token_abc123",
            "google_id": "google_123456789",
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["user"]["name"], "Học Viên Token")
        self.assertEqual(data["user"]["email"], "tokenuser@google-test.test")

