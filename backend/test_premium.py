"""Unit tests for HanziGo Premium, SePay integration, and Vouchers."""
import os
import sqlite3
import uuid
from unittest.mock import patch
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
        self.env = patch.dict(os.environ, {'SEPAY_MERCHANT_ID': '', 'SEPAY_SECRET_KEY': '', 'TURSO_DATABASE_URL': '', 'HANZIGO_DB_DRIVER': 'sqlite'})
        self.env.start()
        self.addCleanup(self.env.stop)
        uri = 'file:legacy-premium-' + uuid.uuid4().hex + '?mode=memory&cache=shared'
        connect = sqlite3.connect
        self.keeper = connect(uri, uri=True)
        self.addCleanup(self.keeper.close)
        connector = patch('database.sqlite3.connect', side_effect=lambda *args, **kwargs: connect(uri, uri=True))
        connector.start()
        self.addCleanup(connector.stop)
        init_db()
        self.client = TestClient(app)

        # Create student user
        now = int(time.time())
        with database() as conn:
            conn.execute("DELETE FROM premium_orders")
            conn.execute("DELETE FROM vouchers")
            conn.execute("DELETE FROM audit_logs WHERE actor_id IN (SELECT id FROM users WHERE email IN ('student_prem@test.com', 'admin_prem@test.com'))")
            conn.execute("DELETE FROM sessions WHERE user_id IN (SELECT id FROM users WHERE email IN ('student_prem@test.com', 'admin_prem@test.com'))")

            conn.execute("DELETE FROM users WHERE email IN ('student_prem@test.com', 'admin_prem@test.com')")
            conn.execute("UPDATE sepay_config SET bank_name='MSB', bank_account='80001795444', account_holder='NGUYEN VO VINH NGUYEN', api_key='', is_active=1 WHERE id=1")


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

    def tearDown(self):
        with database() as conn:
            conn.execute(
                """UPDATE sepay_config SET bank_name='MSB', bank_account='80001795444',
                   account_holder='NGUYEN VO VINH NGUYEN', merchant_id='SP-LIVE-O573535',
                   api_key='spsk_live_paj8JXvTF1ouCh8HeE4mRevPMmX1Ei1o', is_active=1 WHERE id=1"""
            )

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
        self.assertEqual(
            data["qr_url"],
            f"https://qr.sepay.vn/img?acc=80001795444&bank=MSB&amount=49000&des={data['order_code']}&template=qronly",
        )
        self.assertEqual(data["bank_name"], "MSB")
        self.assertEqual(data["bank_account"], "80001795444")
        self.assertEqual(data["account_holder"], "NGUYEN VO VINH NGUYEN")
        self.assertEqual(data["transfer_content"], data["order_code"])
        self.assertEqual(data["expires_in"], 1800)

    def test_one_year_order_qr_amount(self):
        res = self.client.post("/api/premium/orders", headers=self.student_headers, json={"plan_type": "1_year"})
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["amount"], 490000)
        self.assertIn("amount=490000", data["qr_url"])
        self.assertIn("bank=MSB", data["qr_url"])

    def test_order_blocked_when_bank_missing(self):
        with database() as conn:
            conn.execute("UPDATE sepay_config SET bank_account='' WHERE id=1")
        res = self.client.post("/api/premium/orders", headers=self.student_headers, json={"plan_type": "1_month"})
        self.assertEqual(res.status_code, 503)

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
        import hashlib, hmac, json

        # Set known API key in test DB
        with database() as conn:
            conn.execute("UPDATE sepay_config SET api_key='spsk_live_test_secret', merchant_id='SP-LIVE-O573535' WHERE id=1")

        # Create an order
        order_res = self.client.post(
            "/api/premium/orders",
            headers=self.student_headers,
            json={"plan_type": "1_month"}
        )
        self.assertEqual(order_res.status_code, 201)
        order = order_res.json()
        order_code = order["order_code"]

        # 1. Ignore outgoing money (transferType: 'out')
        out_payload = {
            "id": 99991230,
            "gateway": "MSB",
            "accountNumber": "80001795444",
            "content": f"Chuyen tien di {order_code}",
            "transferType": "out",
            "transferAmount": 49000,
        }
        res_out = self.client.post("/api/payment/sepay-webhook", json=out_payload, headers={"Authorization": "Apikey spsk_live_test_secret"})
        self.assertEqual(res_out.status_code, 200)
        self.assertTrue(res_out.json().get("ignored"))

        # Order must still be pending
        st_res = self.client.get(f"/api/premium/orders/{order_code}/status", headers=self.student_headers)
        self.assertFalse(st_res.json()["is_completed"])

        # 2. Reject underpaid amount (transferAmount: 20,000 < 49,000)
        underpaid_payload = {
            "id": 99991231,
            "gateway": "MSB",
            "accountNumber": "80001795444",
            "content": f"Thanh toan thieu {order_code}",
            "transferType": "in",
            "transferAmount": 20000,
        }
        res_under = self.client.post("/api/payment/sepay-webhook", json=underpaid_payload, headers={"Authorization": "Apikey spsk_live_test_secret"})
        self.assertEqual(res_under.status_code, 200)
        self.assertFalse(res_under.json()["success"])

        # Order must still be pending
        st_res = self.client.get(f"/api/premium/orders/{order_code}/status", headers=self.student_headers)
        self.assertFalse(st_res.json()["is_completed"])

        # 3. Reject invalid auth key
        res_bad_auth = self.client.post("/api/payment/sepay-webhook", json=out_payload, headers={"Authorization": "Apikey wrong_key"})
        self.assertEqual(res_bad_auth.status_code, 401)

        # 4. Successful incoming payment with HMAC signature
        valid_payload = {
            "id": 99991234,
            "gateway": "MSB",
            "transactionDate": "2026-10-03 20:00:00",
            "accountNumber": "80001795444",
            "code": None,
            "content": f"Chuyen khoan mua HanziGo {order_code} thanh cong",
            "transferType": "in",
            "transferAmount": 49000,
            "referenceCode": "FT261003TEST",
        }
        raw_body = json.dumps(valid_payload).encode("utf-8")
        timestamp = "1727960000"
        sig = hmac.new(b"spsk_live_test_secret", f"{timestamp}.".encode("utf-8") + raw_body, hashlib.sha256).hexdigest()

        hook_res = self.client.post(
            "/api/payment/sepay-webhook",
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "X-SePay-Signature": f"sha256={sig}",
                "X-SePay-Timestamp": timestamp
            }
        )
        self.assertEqual(hook_res.status_code, 200)
        self.assertTrue(hook_res.json()["success"])

        # Verify order status polling immediately completed
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
        self.assertTrue(len(cfg_data["config"]["bank_name"]) > 0)
        self.assertGreater(len(cfg_data["instructions"]), 3)

        # Update SePay Config
        up_res = self.client.put(
            "/api/admin/premium/sepay-config",
            headers=self.admin_headers,
            json={
                "bank_name": "Vietcombank",
                "bank_account": "101999888",
                "account_holder": "NGUYEN VO VINH NGUYEN",
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

    def test_admin_cannot_manually_activate_transaction(self):
        # Create an order
        order_res = self.client.post("/api/premium/orders", headers=self.student_headers, json={"plan_type": "1_month"})
        self.assertEqual(order_res.status_code, 201)
        order_id = order_res.json()["id"]

        # Admin attempting manual activation must receive 403 Forbidden
        act_res = self.client.post(f"/api/admin/premium/transactions/{order_id}/activate", headers=self.admin_headers)
        self.assertEqual(act_res.status_code, 403)
        self.assertIn("Không thể thao tác thủ công", act_res.json()["detail"])

    def test_admin_grant_and_revoke_student_premium(self):
        # 1. Admin grants VIP (30 days + 2 streak freezes)
        grant_res = self.client.post(
            f"/api/admin/users/{self.student_id}/premium",
            headers=self.admin_headers,
            json={
                "action": "grant",
                "duration_days": 30,
                "added_freezes": 2,
                "note": "Ban phát tặng học viên chăm chỉ"
            }
        )
        self.assertEqual(grant_res.status_code, 200)
        grant_data = grant_res.json()
        self.assertTrue(grant_data["success"])
        self.assertTrue(grant_data["user"]["is_premium"])
        self.assertGreater(grant_data["user"]["premium_until"], int(time.time()))
        self.assertEqual(grant_data["user"]["streak_freezes"], 2)

        # 2. Check public user via /api/admin/users
        users_res = self.client.get(f"/api/admin/users?search=student_prem@test.com", headers=self.admin_headers)
        self.assertEqual(users_res.status_code, 200)
        student_record = users_res.json()[0]
        self.assertTrue(student_record["is_premium"])

        # 3. Admin revokes VIP
        revoke_res = self.client.post(
            f"/api/admin/users/{self.student_id}/premium",
            headers=self.admin_headers,
            json={"action": "revoke"}
        )
        self.assertEqual(revoke_res.status_code, 200)
        revoke_data = revoke_res.json()
        self.assertTrue(revoke_data["success"])
        self.assertFalse(revoke_data["user"]["is_premium"])
        self.assertEqual(revoke_data["user"]["premium_until"], 0)

    def test_pending_order_expires_after_30_minutes_and_is_retained(self):
        # Create an order
        res = self.client.post("/api/premium/orders", headers=self.student_headers, json={"plan_type": "1_month"})
        self.assertEqual(res.status_code, 201)
        code = res.json()["order_code"]

        # Backdate order created_at to 305 seconds ago (over 5 minutes)
        with database() as conn:
            conn.execute("UPDATE premium_orders SET created_at = ? WHERE order_code = ?", (int(time.time()) - 1805, code))

        # Check order status -> should report expired
        status_res = self.client.get(f"/api/premium/orders/{code}/status", headers=self.student_headers)
        self.assertEqual(status_res.status_code, 200)
        status_data = status_res.json()
        self.assertTrue(status_data["is_expired"])
        self.assertEqual(status_data["status"], "expired")

        # Verify order was deleted from premium_orders table
        with database() as conn:
            row = conn.execute("SELECT * FROM premium_orders WHERE order_code = ?", (code,)).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["status"], "cancelled")


if __name__ == "__main__":
    unittest.main()


