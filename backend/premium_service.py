"""HanziGo Premium & SePay payment and voucher service."""
import re
import secrets
import time
from typing import Any
from fastapi import HTTPException

# Plan definitions
PLAN_PRICES = {
    "1_month": {
        "name": "HanziGo Premium · 1 Tháng",
        "price": 49000,
        "duration_days": 30,
        "freeze_grants": 3,
        "description": "49.000 VNĐ / tháng"
    },
    "1_year": {
        "name": "HanziGo Premium · 1 Năm (Tiết kiệm 2 tháng)",
        "price": 490000,
        "duration_days": 365,
        "freeze_grants": 12,
        "description": "490.000 VNĐ / năm (Chỉ ~40.800đ/tháng)"
    }
}

COMPARISON_FEATURES = [
    {
        "category": "Nhóm chức năng",
        "feature": "AI tạo đề thi",
        "free": "3 đề / ngày",
        "premium": "Không giới hạn",
        "highlight": True
    },
    {
        "category": "Tùy biến học tập",
        "feature": "Tùy biến đầu cọ (Bút lông, bút mực, cọ thư pháp)",
        "free": "Cọ mặc định",
        "premium": "Mở khóa toàn bộ"
    },
    {
        "category": "Kho học liệu & Từ vựng",
        "feature": "Lộ trình HSK (HSK 1 đến HSK 6/9)",
        "free": "Chỉ HSK 1 – 6",
        "premium": "Trọn bộ HSK 1 – 9 & Giao tiếp (làm thêm HSK 7-9)",
        "highlight": True
    },
    {
        "category": "Giao diện",
        "feature": "Tùy chọn giao diện màu sắc",
        "free": "Không có",
        "premium": "Tất cả màu"
    },
    {
        "category": "Đặc quyền tài khoản",
        "feature": "Đóng băng chuỗi ngày học (Streak Freeze)",
        "free": "Mất chuỗi nếu quên học",
        "premium": "Tặng 3 lượt bảo lưu / tháng"
    },
    {
        "category": "Huy hiệu & Vinh danh",
        "feature": "Huy hiệu & Khung đại diện Premium",
        "free": "Giao diện thường",
        "premium": "Huy hiệu Premium mạ vàng",
        "highlight": True
    }
]


def generate_ai_voucher_code(conn) -> str:
    """Generate voucher code for AI rewards: format HZG followed by 10 random digits (regex ^HZG\\d{10}$)."""
    for _ in range(50):
        random_digits = "".join(str(secrets.randbelow(10)) for _ in range(10))
        code = f"HZG{random_digits}"
        exists = conn.execute("SELECT 1 FROM vouchers WHERE code = ?", (code,)).fetchone()
        if not exists:
            return code
    # Fallback with timestamp
    return f"HZG{int(time.time()*1000)%10000000000:010d}"


def create_ai_100_score_voucher(conn, user_id: int) -> dict[str, Any]:
    """Auto-generate 30% discount voucher for 1-month Premium when scoring 100 on an exam."""
    code = generate_ai_voucher_code(conn)
    now = int(time.time())
    expires_at = now + 30 * 86400  # 30 days validity
    conn.execute(
        """INSERT INTO vouchers (
            code, discount_percent, is_free_month, max_uses, used_count,
            created_by, user_id, description, is_active, expires_at, created_at
        ) VALUES (?, 30, 0, 1, 0, 'ai', ?, ?, 1, ?, ?)""",
        (
            code,
            user_id,
            "Thưởng AI: Đạt điểm tuyệt đối 100/100 (Giảm 30% gói 1 tháng HanziGo Premium)",
            expires_at,
            now,
        )
    )
    row = conn.execute("SELECT * FROM vouchers WHERE code = ?", (code,)).fetchone()
    return dict(row)


def get_sepay_config(conn) -> dict[str, Any]:
    """Retrieve or initialize default SePay configuration."""
    row = conn.execute("SELECT * FROM sepay_config WHERE id = 1").fetchone()
    if not row:
        conn.execute(
            """INSERT OR IGNORE INTO sepay_config (id, bank_name, bank_account, account_holder, api_key, is_active)
               VALUES (1, 'MBBank', '0399888999', 'NGUYEN VO VINH NIEN', '', 1)"""
        )
        row = conn.execute("SELECT * FROM sepay_config WHERE id = 1").fetchone()
    return dict(row)


def update_sepay_config(conn, bank_name: str, bank_account: str, account_holder: str, api_key: str = "", is_active: int = 1) -> dict[str, Any]:
    """Update SePay configuration in database."""
    conn.execute(
        """UPDATE sepay_config
           SET bank_name = ?, bank_account = ?, account_holder = ?, api_key = ?, is_active = ?, version = version + 1
           WHERE id = 1""",
        (bank_name.strip(), bank_account.strip(), account_holder.strip(), api_key.strip(), is_active)
    )
    return get_sepay_config(conn)


def build_vietqr_url(bank_name: str, bank_account: str, amount: int, order_code: str) -> str:
    """Generate VietQR image URL formatted for SePay."""
    clean_bank = bank_name.strip().replace(" ", "")
    clean_acc = bank_account.strip().replace(" ", "")
    return f"https://qr.sepay.vn/img?acc={clean_acc}&bank={clean_bank}&amount={amount}&des={order_code}"


def create_premium_order(conn, user_id: int, plan_type: str, voucher_code: str | None = None) -> dict[str, Any]:
    """Create a new payment order for HanziGo Premium with optional voucher code."""
    if plan_type not in PLAN_PRICES:
        raise HTTPException(400, "Gói hội viên không hợp lệ. Vui lòng chọn 1_month hoặc 1_year.")

    plan_info = PLAN_PRICES[plan_type]
    original_amount = plan_info["price"]
    discount_percent = 0
    clean_voucher = voucher_code.strip().upper() if voucher_code else None
    matched_voucher = None

    if clean_voucher:
        voucher_row = conn.execute("SELECT * FROM vouchers WHERE UPPER(code) = ?", (clean_voucher,)).fetchone()
        if not voucher_row:
            raise HTTPException(400, f"Mã voucher '{clean_voucher}' không tồn tại.")
        matched_voucher = dict(voucher_row)
        if not matched_voucher["is_active"]:
            raise HTTPException(400, "Mã voucher này đã bị vô hiệu hóa.")
        now = int(time.time())
        if matched_voucher["expires_at"] > 0 and now > matched_voucher["expires_at"]:
            raise HTTPException(400, "Mã voucher này đã hết hạn sử dụng.")
        if matched_voucher["used_count"] >= matched_voucher["max_uses"]:
            raise HTTPException(400, "Mã voucher này đã hết lượt sử dụng.")

        if matched_voucher["is_free_month"]:
            if plan_type != "1_month":
                raise HTTPException(400, "Mã voucher 1 tháng miễn phí chỉ áp dụng cho gói 1 Tháng.")
            discount_percent = 100
        else:
            discount_percent = matched_voucher["discount_percent"]

    amount = max(0, round(original_amount * (100 - discount_percent) / 100))

    # Generate unique order code: HZG + 6 random digits
    for _ in range(50):
        code = f"HZG{secrets.randbelow(900000) + 100000}"
        if not conn.execute("SELECT 1 FROM premium_orders WHERE order_code = ?", (code,)).fetchone():
            break
    else:
        code = f"HZG{int(time.time())%1000000:06d}"

    now = int(time.time())
    order_id = conn.execute(
        """INSERT INTO premium_orders (
            order_code, user_id, plan_type, amount, original_amount,
            voucher_code, discount_percent, status, payment_gateway,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', 'sepay', ?)""",
        (code, user_id, plan_type, amount, original_amount, clean_voucher, discount_percent, now)
    ).lastrowid

    # If amount is 0 (e.g. 100% discount / free month via order)
    if amount == 0:
        return complete_premium_order(conn, code, sepay_reference_code="FREE_VOUCHER")

    cfg = get_sepay_config(conn)
    qr_url = build_vietqr_url(cfg["bank_name"], cfg["bank_account"], amount, code)

    return {
        "id": order_id,
        "order_code": code,
        "plan_type": plan_type,
        "plan_name": plan_info["name"],
        "amount": amount,
        "original_amount": original_amount,
        "discount_percent": discount_percent,
        "voucher_code": clean_voucher,
        "status": "pending",
        "bank_name": cfg["bank_name"],
        "bank_account": cfg["bank_account"],
        "account_holder": cfg["account_holder"],
        "transfer_content": code,
        "qr_url": qr_url,
        "created_at": now
    }


def complete_premium_order(conn, order_id_or_code: int | str, sepay_transaction_id: str | None = None, sepay_reference_code: str | None = None) -> dict[str, Any]:
    """Mark order as completed, grant Premium duration and streak freezes to user."""
    if isinstance(order_id_or_code, int) or (isinstance(order_id_or_code, str) and order_id_or_code.isdigit()):
        row = conn.execute("SELECT * FROM premium_orders WHERE id = ?", (int(order_id_or_code),)).fetchone()
    else:
        row = conn.execute("SELECT * FROM premium_orders WHERE order_code = ?", (str(order_id_or_code).strip(),)).fetchone()

    if not row:
        raise HTTPException(404, "Không tìm thấy đơn hàng.")

    order = dict(row)
    now = int(time.time())

    if order["status"] == "completed":
        # Already completed, fetch user
        user = conn.execute("SELECT * FROM users WHERE id = ?", (order["user_id"],)).fetchone()
        return {
            **order,
            "is_completed": True,
            "premium_until": user["premium_until"] if user else 0,
            "streak_freezes": user["streak_freezes"] if user else 0
        }

    plan_info = PLAN_PRICES.get(order["plan_type"], PLAN_PRICES["1_month"])
    user_row = conn.execute("SELECT * FROM users WHERE id = ?", (order["user_id"],)).fetchone()
    if not user_row:
        raise HTTPException(404, "Không tìm thấy người dùng.")

    user = dict(user_row)
    current_until = user.get("premium_until") or 0
    base_time = max(now, current_until)
    new_until = base_time + plan_info["duration_days"] * 86400
    added_freezes = plan_info["freeze_grants"]

    # Update user
    conn.execute(
        """UPDATE users
           SET premium_until = ?, streak_freezes = streak_freezes + ?, version = version + 1
           WHERE id = ?""",
        (new_until, added_freezes, user["id"])
    )

    # Update order
    conn.execute(
        """UPDATE premium_orders
           SET status = 'completed', completed_at = ?,
               sepay_transaction_id = COALESCE(?, sepay_transaction_id),
               sepay_reference_code = COALESCE(?, sepay_reference_code)
           WHERE id = ?""",
        (now, sepay_transaction_id, sepay_reference_code, order["id"])
    )

    # Increment voucher usage if applicable
    if order.get("voucher_code"):
        conn.execute(
            """UPDATE vouchers SET used_count = used_count + 1 WHERE UPPER(code) = ?""",
            (order["voucher_code"].upper(),)
        )

    order["status"] = "completed"
    order["completed_at"] = now
    order["premium_until"] = new_until
    order["streak_freezes"] = user.get("streak_freezes", 0) + added_freezes
    return order


def redeem_voucher_direct(conn, user_id: int, code: str) -> dict[str, Any]:
    """Redeem a voucher directly: activate 1 free month or validate % discount for order."""
    clean_code = code.strip().upper()
    row = conn.execute("SELECT * FROM vouchers WHERE UPPER(code) = ?", (clean_code,)).fetchone()
    if not row:
        raise HTTPException(400, f"Mã voucher '{clean_code}' không hợp lệ hoặc không tồn tại.")

    voucher = dict(row)
    now = int(time.time())

    if not voucher["is_active"]:
        raise HTTPException(400, "Mã voucher này đã bị vô hiệu hóa.")
    if voucher["expires_at"] > 0 and now > voucher["expires_at"]:
        raise HTTPException(400, "Mã voucher này đã hết hạn sử dụng.")
    if voucher["used_count"] >= voucher["max_uses"]:
        raise HTTPException(400, "Mã voucher này đã hết số lần sử dụng.")

    # Free 1-month voucher: activate immediately without bank payment!
    if voucher["is_free_month"]:
        user_row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user_row:
            raise HTTPException(404, "Không tìm thấy người dùng.")

        user = dict(user_row)
        current_until = user.get("premium_until") or 0
        base_time = max(now, current_until)
        new_until = base_time + 30 * 86400

        conn.execute(
            """UPDATE users
               SET premium_until = ?, streak_freezes = streak_freezes + 3, version = version + 1
               WHERE id = ?""",
            (new_until, user_id)
        )
        conn.execute(
            """UPDATE vouchers SET used_count = used_count + 1 WHERE id = ?""",
            (voucher["id"],)
        )

        return {
            "success": True,
            "type": "free_month",
            "message": "🎉 Chúc mừng! Bạn đã nhận thành công 1 tháng HanziGo Premium miễn phí!",
            "premium_until": new_until,
            "is_premium": True,
            "streak_freezes_added": 3
        }

    # Percentage discount voucher: validate and report savings
    discount_pct = voucher["discount_percent"]
    discounted_1_month = max(0, round(49000 * (100 - discount_pct) / 100))
    discounted_1_year = max(0, round(490000 * (100 - discount_pct) / 100))

    return {
        "success": True,
        "type": "discount",
        "code": voucher["code"],
        "discount_percent": discount_pct,
        "discounted_1_month": discounted_1_month,
        "discounted_1_year": discounted_1_year,
        "message": f"Mã '{voucher['code']}' hợp lệ! Bạn được giảm {discount_pct}% khi đăng ký gói HanziGo Premium.",
        "created_by": voucher["created_by"]
    }


def process_sepay_webhook(conn, payload: dict[str, Any], auth_header: str | None = None) -> dict[str, Any]:
    """Process incoming bank transfer notification from SePay webhook."""
    cfg = get_sepay_config(conn)

    # Optional token verification if admin configured an API key
    configured_key = cfg.get("api_key", "").strip()
    if configured_key:
        # SePay typically passes 'Apikey <token>' or bearer token
        token_match = False
        if auth_header:
            clean_token = auth_header.replace("Apikey", "").replace("Bearer", "").strip()
            token_match = (clean_token == configured_key)
        if not token_match:
            # Check payload query or token field
            if payload.get("token") == configured_key:
                token_match = True
        if not token_match:
            raise HTTPException(401, "SePay API key không hợp lệ.")

    # Only process incoming money ('in')
    transfer_type = payload.get("transferType", "in")
    if str(transfer_type).lower() != "in":
        return {"success": True, "message": "Bỏ qua giao dịch không phải tiền vào (transferType != 'in')."}

    content = str(payload.get("content", ""))
    transfer_amount = int(payload.get("transferAmount", 0) or 0)
    sepay_tx_id = str(payload.get("id", ""))
    sepay_ref = str(payload.get("referenceCode", ""))

    # Find pending order matching order code in content
    # Order code format: HZG\d{6} or custom
    matches = re.findall(r"HZG[0-9A-Z_]+", content, re.IGNORECASE)
    matched_order = None

    if matches:
        for candidate in matches:
            row = conn.execute(
                """SELECT * FROM premium_orders WHERE UPPER(order_code) = UPPER(?) AND status = 'pending'""",
                (candidate.strip(),)
            ).fetchone()
            if row:
                matched_order = dict(row)
                break

    # If no regex match, search all pending orders to check if order_code is in content
    if not matched_order:
        pending_rows = conn.execute("SELECT * FROM premium_orders WHERE status = 'pending'").fetchall()
        for p in pending_rows:
            p_dict = dict(p)
            if p_dict["order_code"].upper() in content.upper():
                matched_order = p_dict
                break

    if not matched_order:
        return {
            "success": True,
            "message": f"Không tìm thấy đơn hàng chờ thanh toán tương ứng trong nội dung: '{content}'."
        }

    # Verify amount
    if transfer_amount < matched_order["amount"]:
        return {
            "success": False,
            "message": f"Số tiền chuyển khoản ({transfer_amount}đ) ít hơn số tiền đơn hàng ({matched_order['amount']}đ)."
        }

    # Complete order & upgrade user
    result = complete_premium_order(
        conn,
        matched_order["id"],
        sepay_transaction_id=sepay_tx_id,
        sepay_reference_code=sepay_ref
    )

    return {
        "success": True,
        "message": "Kích hoạt HanziGo Premium thành công qua SePay.",
        "order_code": matched_order["order_code"],
        "user_id": matched_order["user_id"],
        "plan_type": matched_order["plan_type"]
    }
