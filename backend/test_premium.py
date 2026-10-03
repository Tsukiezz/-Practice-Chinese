"""Unit tests for HanziGo Premium, SePay integration, and Vouchers."""
import re
import time
import unittest
from fastapi.testclient import TestClient

from database import database, init_db
from main import app
from premium_service import (
    PLAN_PRICES,
    create_ai_100_score_voucher,
    generate_ai_voucher_code,
    get_sepay_config,
    update_sepay_config,
    create_premium_order,
    complete_premium_order,
    redeem_voucher_direct,
    process_sepay_webhook,
)


class TestPremiumSystem(unittest.TestCase):
    def setUp(self):
        init_db()
        self.client = TestClient(app)

        # Create student user
        now = int(time.time())
        with database() as conn:
            # Clean up test records
            conn.execute("DELETE FROM premium_orders")
            conn.execute("DELETE FROM vouchers")
            conn.execute("DELETE FROM sessions WHERE user_id IN (SELECT id FROM users WHERE email IN ('student_prem@test.com', 'admin_prem@test.com'))")
            conn.execute("DELETE FROM users WHERE email IN ('student_prem@test.com', 'admin_prem@test.com')")
            conn.execute("UPDATE sepay_config SET bank_name='MBBank', bank_account='0399888999', account_holder='NGUYEN VO VINH NIEN', api_key='', is_active=1 WHERE id=1")

            # Create test student
            self.student_id = conn.execute(
                """INSERT INTO users(name, email, password_hash, salt, role, is_active, created_at, premium_until, streak_freezes)
                   VALUES('Student Premium', 'student_prem@test.com', 'hash', 'salt', 'student', 1, ?, 0, 0)""",
                (now,)
            ).lastrowid

            # Create test admin
            self.admin_id = conn.execute(
                """INSERT INTO users(name, email, password_hash, salt, role, is_active, created_at, premium_until, streak_freezes)
                   VALUES('Admin Premium', 'admin_prem@test.com', 'hash', 'salt', 'admin', 1, ?, 0, 0)""",
                (now,)
            ).lastrowid

            # Login sessions
            import hashlib, secrets
            self.student_token = secrets.token_urlsafe(32)
            conn.execute(
                "INSERT INTO sessions VALUES(?, ?, ?)",
                (hashlib.sha256(self.student_token.encode()).hexdigest(), self.student_id, now + 86400)
            )

            self.admin_token = secrets.token_urlsafe(32)
            conn.execute(
                "INSERT INTO sessions VALUES(?, ?, ?)",
                (hashlib.sha256(self.admin_token.encode()).hexdigest(), self.admin_id, now + 86400)
            )

        self.student_headers = {"Authorization": f"Bearer {self.student_token}"}
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}

    def test_plans_endpoint(self):
        res = self.client.get("/api/premium/plans")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("1_month", data["plans"])
        self.assertIn("1_year", data["plans"])
        self.assertEqual(data["plans"]["1_month"]["price"], 49000)
        self.assertEqual(data["plans"]["1_year"]["price"], 490000)
        self.assertGreaterEqual(len(data["comparison"]), 6)

    def test_ai_voucher_format_and_generation(self):
        with database() as conn:
            voucher = create_ai_100_score_voucher(conn, self.student_id)

        # AI voucher must have format HZG__________ (HZG + exactly 10 random numbers)
        self.assertTrue(re.match(r"^HZG\d{10}$", voucher["code"]), f"Invalid AI voucher code: {voucher['code']}")
        self.assertEqual(voucher["discount_percent"], 30)
        self.assertEqual(voucher["is_free_month"], 0)
        self.assertEqual(voucher["created_by"], "ai")

    def test_order_creation_and_sepay_qr(self):
        res = self.client.post(
            "/api/premium/orders",
            headers=self.student_headers,
            json={"plan_type": "1_month"}
        )
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["amount"], 49000)
        self.assertEqual(data["original_amount"], 49000)
        self.assertTrue(data["order_code"].startswith("HZG"))
        self.assertIn("qr.sepay.vn", data["qr_url"])

    def test_order_creation_with_discount_voucher(self):
        # Admin creates 20% voucher
        with database() as conn:
            conn.execute(
                """INSERT INTO vouchers (code, discount_percent, is_free_month, max_uses, used_count, created_by, is_active, created_at)
                   VALUES ('GIAM20', 20, 0, 1, 0, 'admin', 1, ?)""",
                (int(time.time()),)
            )

        res = self.client.post(
            "/api/premium/orders",
            headers=self.student_headers,
            json={"plan_type": "1_month", "voucher_code": "GIAM20"}
        )
        self.assertEqual(res.status_code, 201)
        data = res.json()
        # 49,000đ - 20% = 39,200đ
        self.assertEqual(data["amount"], 39200)
        self.assertEqual(data["discount_percent"], 20)

    def test_redeem_free_month_voucher_directly(self):
        # Admin creates a 1-month free voucher
        with database() as conn:
            conn.execute(
                """INSERT INTO vouchers (code, discount_percent, is_free_month, max_uses, used_count, created_by, is_active, created_at)
                   VALUES ('FREEMONTH1', 100, 1, 1, 0, 'admin', 1, ?)""",
                (int(time.time()),)
            )

        res = self.client.post(
            "/api/premium/redeem-voucher",
            headers=self.student_headers,
            json={"code": "FREEMONTH1"}
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["type"], "free_month")

        # Check user is now premium with streak freezes
        user_res = self.client.get("/api/premium/me", headers=self.student_headers)
        self.assertEqual(user_res.status_code, 200)
        user_data = user_res.json()
        self.assertTrue(user_data["is_premium"])
        self.assertGreater(user_data["days_remaining"], 28)
        self.assertEqual(user_data["streak_freezes"], 3)

    def test_sepay_webhook_flow(self):
        # Create an order
        order_res = self.client.post(
            "/api/premium/orders",
            headers=self.student_headers,
            json={"plan_type": "1_month"}
        )
        self.assertEqual(order_res.status_code, 201)
        order = order_res.json()
        order_code = order["order_code"]

        # Simulate SePay webhook callback
        webhook_payload = {
            "id": 99991234,
            "gateway": "MBBank",
            "transactionDate": "2026-10-03 20:00:00",
            "accountNumber": "0399888999",
            "code": None,
            "content": f"Chuyen khoan mua HanziGo {order_code} thanh cong",
            "transferType": "in",
            "transferAmount": 49000,
            "referenceCode": "FT261003TEST",
        }

        hook_res = self.client.post("/api/payment/sepay-webhook", json=webhook_payload)
        self.assertEqual(hook_res.status_code, 200)
        self.assertTrue(hook_res.json()["success"])

        # Verify order status polling
        status_res = self.client.get(f"/api/premium/orders/{order_code}/status", headers=self.student_headers)
        self.assertEqual(status_res.status_code, 200)
        status_data = status_res.json()
        self.assertTrue(status_data["is_completed"])
        self.assertEqual(status_data["status"], "completed")
        self.assertTrue(status_data["is_premium"])

    def test_admin_endpoints(self):
        # Dashboard
        dash = self.client.get("/api/admin/premium/dashboard", headers=self.admin_headers)
        self.assertEqual(dash.status_code, 200)

        # SePay Config & Instructions
        cfg_res = self.client.get("/api/admin/premium/sepay-config", headers=self.admin_headers)
        self.assertEqual(cfg_res.status_code, 200)
        cfg_data = cfg_res.json()
        self.assertIn("MBBank", cfg_data["config"]["bank_name"])
        self.assertGreater(len(cfg_data["instructions"]), 3)

        # Update SePay Config
        up_res = self.client.put(
            "/api/admin/premium/sepay-config",
            headers=self.admin_headers,
            json={
                "bank_name": "Vietcombank",
                "bank_account": "101999888",
                "account_holder": "NGUYEN VO VINH NIEN",
                "api_key": "test_sepay_token_123",
                "is_active": 1
            }
        )
        self.assertEqual(up_res.status_code, 200)
        self.assertEqual(up_res.json()["config"]["bank_name"], "Vietcombank")

        # Admin Create Voucher
        v_res = self.client.post(
            "/api/admin/premium/vouchers",
            headers=self.admin_headers,
            json={
                "code": "TESTADMIN50",
                "discount_percent": 50,
                "is_free_month": False,
                "max_uses": 5,
                "description": "Admin giam 50%"
            }
        )
        self.assertEqual(v_res.status_code, 201)
        created_v = v_res.json()
        self.assertEqual(created_v["code"], "TESTADMIN50")
        self.assertEqual(created_v["discount_percent"], 50)

        # List Vouchers
        list_v = self.client.get("/api/admin/premium/vouchers", headers=self.admin_headers)
        self.assertEqual(list_v.status_code, 200)
        codes = [item["code"] for item in list_v.json()["items"]]
        self.assertIn("TESTADMIN50", codes)


if __name__ == "__main__":
    unittest.main()
