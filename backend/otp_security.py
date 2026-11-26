"""Shared, database-backed OTP protection for registration and password recovery."""
import hashlib
import hmac
import ipaddress
import json
import os
import re
import secrets
import time

from fastapi import HTTPException
from database import audit, database

TTL_SECONDS = 600
MAX_ATTEMPTS = 5
_DEV_SECRET = secrets.token_bytes(48)
INVALID_CODE = "Mã xác thực không chính xác, đã hết hạn hoặc vượt quá 5 lần thử."
RESET_MESSAGE = "Nếu email thuộc tài khoản đang hoạt động, mã xác nhận sẽ được gửi. Vui lòng kiểm tra cả thư rác."


def now():
    return int(time.time())


def _secret():
    value = os.getenv("OTP_HASH_SECRET", "")
    if len(value) >= 32:
        return value.encode()
    if os.getenv("VERCEL"):
        raise HTTPException(503, "Dịch vụ xác thực chưa sẵn sàng. Vui lòng thử lại sau.")
    return _DEV_SECRET


def encode_code(email, purpose, code, nonce=None):
    nonce = nonce or secrets.token_hex(16)
    message = json.dumps([email, purpose, nonce, code], separators=(",", ":")).encode()
    digest = hmac.new(_secret(), message, hashlib.sha256).hexdigest()
    return f"h1${nonce}${digest}"


def matches_code(email, purpose, code, stored):
    parts = stored.split("$")
    if len(parts) != 3 or parts[0] != "h1" or len(parts[1]) != 32:
        return False
    return hmac.compare_digest(encode_code(email, purpose, code, parts[1]), stored)


def migrate_legacy_codes(conn):
    """Upgrade old plaintext records privately; never log or export their values."""
    if os.getenv("VERCEL") and len(os.getenv("OTP_HASH_SECRET", "")) < 32:
        return  # OTP endpoints fail closed until the server secret is configured.
    conn.execute("UPDATE verification_codes SET code='',temp_data_json='{}',used=1 WHERE expires_at<=?", (now(),))
    rows = conn.execute("SELECT id,email,purpose,code FROM verification_codes WHERE length(code)=6").fetchall()
    for row in rows:
        if re.fullmatch(r"[0-9]{6}", row["code"]):
            conn.execute("UPDATE verification_codes SET code=? WHERE id=? AND code=?",
                         (encode_code(row["email"], row["purpose"], row["code"]), row["id"], row["code"]))


def client_ip(request):
    # Only trust the platform-overwritten header when actually running on Vercel.
    if os.getenv("VERCEL"):
        candidate = request.headers.get("x-vercel-forwarded-for", "").split(",")[0].strip()
        try:
            return str(ipaddress.ip_address(candidate))
        except ValueError:
            pass
    return str(request.client.host if request.client else "unknown")


def _scope(value):
    return hashlib.sha256(value.encode()).hexdigest()


def _limits(rules):
    """Serialize reservations across instances; a rejected request never undoes counters."""
    stamp, retry = now(), 0
    with database() as conn:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("DELETE FROM request_limits WHERE key LIKE 'otp:%' AND window<?", (stamp - 86400,))
        states = []
        for key, maximum, seconds in rules:
            row = conn.execute("SELECT window,count FROM request_limits WHERE key=?", (key,)).fetchone()
            active = row is not None and stamp - row["window"] < seconds
            if active and row["count"] >= maximum:
                retry = max(retry, row["window"] + seconds - stamp)
            states.append((key, row, active))
        if not retry:
            for key, row, active in states:
                if active:
                    conn.execute("UPDATE request_limits SET count=count+1 WHERE key=?", (key,))
                else:
                    conn.execute("INSERT OR REPLACE INTO request_limits(key,window,count) VALUES(?,?,1)", (key, stamp))
    if retry:
        raise HTTPException(429, f"Bạn thao tác quá nhanh. Vui lòng thử lại sau {retry} giây.",
                            headers={"Retry-After": str(retry)})


def limit_send(email, purpose, request):
    _secret()
    email_key, ip_key = _scope(email), _scope(client_ip(request))
    _limits([(f"otp:cooldown:{purpose}:{email_key}", 1, 60),
             (f"otp:send-email:{email_key}", 5, 3600),
             (f"otp:send-ip-hour:{ip_key}", 30, 3600),
             (f"otp:send-ip-minute:{ip_key}", 10, 60)])


def create_code(conn, email, purpose, data):
    code = f"{secrets.randbelow(1_000_000):06d}"
    stamp = now()
    row_id = conn.execute("""INSERT INTO verification_codes
        (email,code,purpose,temp_data_json,expires_at,created_at,used)
        VALUES(?,?,?,?,?,?,1)""", (email, encode_code(email, purpose, code), purpose,
        json.dumps(data, ensure_ascii=False), stamp + TTL_SECONDS, stamp)).lastrowid
    return row_id, code


def deliver_code(row_id, email, purpose, code, send):
    try:
        if not send(email, code, purpose):
            raise RuntimeError("Delivery was not accepted")
    except Exception:
        with database() as conn:
            conn.execute("UPDATE verification_codes SET expires_at=0,temp_data_json='{}' WHERE id=?", (row_id,))
        raise HTTPException(503, "Chưa gửi được mã xác thực. Vui lòng thử lại sau.") from None
    with database() as conn:
        conn.execute("BEGIN IMMEDIATE")
        pending = conn.execute("SELECT id FROM verification_codes WHERE id=? AND expires_at>?", (row_id, now())).fetchone()
        newer = conn.execute("SELECT id FROM verification_codes WHERE email=? AND purpose=? AND id>? AND used=0",
                             (email, purpose, row_id)).fetchone()
        if pending and not newer:
            conn.execute("UPDATE verification_codes SET used=1,expires_at=0,temp_data_json='{}' WHERE email=? AND purpose=? AND id<?",
                         (email, purpose, row_id))
            conn.execute("UPDATE verification_codes SET used=0 WHERE id=?", (row_id,))


def consume_code(email, purpose, code, request, on_verified):
    _secret()
    _limits([(f"otp:verify-ip:{_scope(client_ip(request))}", 60, 60),
             (f"otp:verify-email:{_scope(email)}", 20, TTL_SECONDS)])
    valid, result = False, None
    with database() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("""SELECT * FROM verification_codes WHERE email=? AND purpose=?
            AND used=0 AND expires_at>? ORDER BY id DESC LIMIT 1""", (email, purpose, now())).fetchone()
        if row and row["attempts"] < MAX_ATTEMPTS:
            stored = row["code"]
            # Compatibility for an in-flight request from the preceding deployment.
            if re.fullmatch(r"[0-9]{6}", stored):
                stored = encode_code(email, purpose, stored)
                conn.execute("UPDATE verification_codes SET code=? WHERE id=?", (stored, row["id"]))
            if matches_code(email, purpose, code, stored):
                result = on_verified(conn, row)
                valid = result is not False
                conn.execute("UPDATE verification_codes SET used=1,expires_at=0,temp_data_json='{}' WHERE email=? AND purpose=?",
                             (email, purpose))
            else:
                conn.execute("""UPDATE verification_codes SET attempts=attempts+1,
                    used=CASE WHEN attempts+1>=? THEN 1 ELSE used END,
                    temp_data_json=CASE WHEN attempts+1>=? THEN '{}' ELSE temp_data_json END WHERE id=?""",
                             (MAX_ATTEMPTS, MAX_ATTEMPTS, row["id"]))
    if not valid:
        raise HTTPException(400, INVALID_CODE)
    return result


def request_password_reset(email, request, send):
    limit_send(email, "forgot_password", request)
    with database() as conn:
        user = conn.execute("SELECT id,password_hash FROM users WHERE email=? AND is_active=1", (email,)).fetchone()
        if user:
            data = {"user_id": user["id"], "credential": hashlib.sha256(user["password_hash"].encode()).hexdigest()}
            row_id, code = create_code(conn, email, "forgot_password", data)
    if user:
        deliver_code(row_id, email, "forgot_password", code, send)
    return {"status": "ok", "message": RESET_MESSAGE}


def reset_password(email, code, password, request, hash_password):
    def apply_reset(conn, row):
        user = conn.execute("SELECT id,password_hash FROM users WHERE email=? AND is_active=1", (email,)).fetchone()
        data = json.loads(row["temp_data_json"])
        if not user:
            return False
        if data and (data.get("user_id") != user["id"] or
                     data.get("credential") != hashlib.sha256(user["password_hash"].encode()).hexdigest()):
            return False
        salt = secrets.token_hex(16)
        conn.execute("UPDATE users SET password_hash=?,salt=?,version=version+1 WHERE id=?",
                     (hash_password(password, salt), salt, user["id"]))
        conn.execute("DELETE FROM sessions WHERE user_id=?", (user["id"],))
        audit(conn, user["id"], "password_recovery", "user", user["id"])
        return True
    consume_code(email, "forgot_password", code, request, apply_reset)
    return {"status": "ok", "message": "Đặt lại mật khẩu thành công. Vui lòng đăng nhập với mật khẩu mới."}
