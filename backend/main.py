"""HanziGo Admin API. Run: python -m uvicorn main:app --port 8010."""
import hashlib
import hmac
import json
import os
import logging
import re
import secrets
import sqlite3
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from stroke_counts import stroke_metadata
from ai_errors import ai_http_error
from database import audit, database, init_db, row_to_dict, ensure_default_admin
from email_service import (get_smtp_status, send_verification_email,
                          smtp_is_configured)
from models import Appeal, AppealReview
from models import (AIConfig, AdminCreateUser, AdminResetPassword, DictionaryLookup, Exam, ExamUpdate,
                    EssayGradeRequest, EssayGradeResponse,
                    ExamCanvasGradeRequest,
                    ForgotPasswordRequest, ForgotPasswordVerify,
                    GrammarAnalysisRequest, GrammarAnalysisResponse,
                    HandwritingGradeResponse,
                    HandwritingRetryItem,
                    HandwritingRecognition, HandwritingRecognitionResponse,
                    HandwritingSubmission, Login, Override, Register,
                    RegisterRequest, RegisterVerify,
                    Submission, UserUpdate, Word, WordUpdate, WritingSubmission,
                    CreatePremiumOrderRequest, RedeemVoucherRequest,
                    SepayConfigUpdate, AdminCreateVoucherRequest, AdminUserPremiumAction)

from premium_service import (
    PLAN_PRICES, COMPARISON_FEATURES,
    create_ai_100_score_voucher, get_sepay_config, update_sepay_config,
    create_premium_order, complete_premium_order, redeem_voucher_direct,
    process_sepay_webhook, cleanup_expired_pending_orders
)

from services import (configured_api_key, configured_model, evaluate_with_ai,
                      compare_handwriting_strokes,
                      gemini_capability_provider, gemini_exam_provider,
                      gemini_essay_provider, gemini_grammar_provider,
                      gemini_handwriting_recognition_provider, gemini_provider,
                      grade_essay_with_ai, grade_handwriting_offline,
                      grade_with_ai, ai_settings,
                      analyze_grammar_with_ai, recognize_handwriting_with_ai,
                      record_ai_usage, build_handwriting_retry_items)


@asynccontextmanager
async def lifespan(app):
    # Cloud schema/data are provisioned once before deployment, not per cold start.
    if os.getenv("VERCEL") and os.getenv("TURSO_DATABASE_URL"):
        with database() as conn:
            conn.execute("SELECT lesson_id FROM lesson_progress LIMIT 1").fetchall()
            from ai_exam import init_ai_exam_tables
            init_ai_exam_tables(conn)
            from ai_reading import init_reading_tables
            init_reading_tables(conn)
            from database import init_auth_tables, init_listening_exams, init_comprehensive_exams, ensure_default_admin
            init_auth_tables(conn)
            init_listening_exams(conn)
            init_comprehensive_exams(conn)
            ensure_default_admin(conn)
    else:
        init_db()
        from vocabulary_catalog import init_catalog, refresh_search
        with database() as conn:
            init_catalog(conn)
            refresh_search(conn)
        from usecase_features import init_features
        init_features()
        from ai_exam import init_ai_exam_tables
        with database() as conn:
            init_ai_exam_tables(conn)
        from ai_reading import init_reading_tables
        with database() as conn:
            init_reading_tables(conn)
        from lesson_catalog import init_lessons
        init_lessons()
        if "unittest" not in sys.modules and not os.getenv("TESTING"):
            from database import init_listening_exams, init_comprehensive_exams, ensure_default_admin
            with database() as conn:
                init_listening_exams(conn)
                init_comprehensive_exams(conn)
                ensure_default_admin(conn)
    from support_chat import init_chat
    init_chat()
    from premium_benefits import init_benefits
    with database() as conn:
        init_benefits(conn)
    yield


from vocabulary_catalog import router as vocabulary_router

app = FastAPI(title="HanziGo · Chinese Learning API", version="1.0.0", lifespan=lifespan)
app.include_router(vocabulary_router)
from support_chat import router as support_chat_router
app.include_router(support_chat_router)
app.add_middleware(CORSMiddleware,
                   allow_origins=os.getenv("FRONTEND_ORIGINS", "http://localhost:5173,http://localhost:8080").split(","),
                   allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
                   allow_headers=["Authorization", "Content-Type"])


def hash_password(password, salt):
    try:
        salt_bytes = bytes.fromhex(salt)
    except (ValueError, TypeError):
        salt_bytes = salt.encode("utf-8") if isinstance(salt, str) else b"00" * 16
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, 600_000).hex()


def public_user(row):
    now = int(time.time())
    keys = row.keys() if hasattr(row, "keys") else row
    p_until = row["premium_until"] if "premium_until" in keys else 0
    is_prem = bool(p_until and p_until > now)
    freezes = 0
    if is_prem:
        from datetime import datetime
        from premium_benefits import LOCAL_TZ
        month = datetime.fromtimestamp(now, LOCAL_TZ).strftime('%Y-%m')
        with database() as conn:
            used = conn.execute('SELECT COUNT(*) FROM streak_protection WHERE user_id=? AND day LIKE ?', (row['id'], month + '%')).fetchone()[0]
        freezes = max(0, 3 - used)
    res = {key: row[key] for key in ("id", "name", "email", "role", "is_active", "created_at", "version")}
    res["premium_until"] = p_until
    res["is_premium"] = is_prem
    res["streak_freezes"] = freezes
    return res


def session(conn, user):
    token = secrets.token_urlsafe(32)
    conn.execute("DELETE FROM sessions WHERE expires_at <= ?", (int(time.time()),))
    conn.execute("INSERT INTO sessions VALUES(?,?,?)",
                 (hashlib.sha256(token.encode()).hexdigest(), user["id"], int(time.time()) + 86400))
    return {"token": token, "user": public_user(user), "expires_in": 86400}


def current_user(authorization: Annotated[str | None, Header()] = None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Vui lòng đăng nhập")
    token_hash = hashlib.sha256(authorization[7:].encode()).hexdigest()
    with database() as conn:
        row = conn.execute("SELECT u.* FROM users u JOIN sessions s ON s.user_id=u.id WHERE s.token_hash=? AND s.expires_at>?",
                           (token_hash, int(time.time()))).fetchone()
    if row is None:
        raise HTTPException(401, "Phiên đăng nhập không hợp lệ hoặc đã hết hạn")
    if not row["is_active"]:
        raise HTTPException(403, "Tài khoản đã bị khóa")
    return row_to_dict(row)


def admin_user(user=Depends(current_user)):
    if user["role"] != "admin":
        raise HTTPException(403, "Chỉ quản trị viên được truy cập")
    return user


def require_row(conn, table, row_id) -> dict[str, Any]:
    # table is always an internal constant, never request input.
    row = conn.execute(f"SELECT * FROM {table} WHERE id=?", (row_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "Không tìm thấy dữ liệu")
    return row_to_dict(row)


def check_version(row, version):
    if row["version"] != version:
        raise HTTPException(409, "Dữ liệu đã được người khác cập nhật. Hãy tải lại trước khi lưu.")


def grade_reading_exam(user_id, content):
    return evaluate_with_ai(user_id, "reading", content, gemini_exam_provider)


def grade_listening_exam(user_id, content):
    return evaluate_with_ai(user_id, "listening", content, gemini_exam_provider)


def grade_comprehensive_exam(user_id, content):
    return evaluate_with_ai(user_id, "exam", content, gemini_exam_provider)


def get_exam_ai_grader():
    """Dependency hook keeps provider calls replaceable in isolated tests."""
    return grade_reading_exam


@app.get("/api/health")
def health():
    with database() as conn:
        conn.execute("SELECT 1").fetchone()
    return {"status": "ok", "product": "HanziGo"}


@app.get("/api/auth/email-status")
def email_status():
    return {
        "status": "ok",
        "smtp": get_smtp_status(),
        "is_vercel": bool(os.getenv("VERCEL")),
    }


@app.post("/api/auth/register", status_code=201)
def register(body: Register):
    if os.getenv("VERCEL"):
        raise HTTPException(400, "Đăng ký yêu cầu xác thực email OTP. Vui lòng sử dụng tính năng đăng ký qua email trên ứng dụng.")
    salt = secrets.token_hex(16)
    password_hash = hash_password(body.password, salt)
    try:
        with database() as conn:
            uid = conn.execute("INSERT INTO users(name,email,password_hash,salt,created_at) VALUES(?,?,?,?,?)",
                               (body.name, body.email, password_hash, salt, int(time.time()))).lastrowid
            return session(conn, require_row(conn, "users", uid))
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Email đã được sử dụng")


@app.post("/api/auth/register-request")
def register_request(body: RegisterRequest):
    with database() as conn:
        existing = conn.execute("SELECT id FROM users WHERE email=?", (body.email.lower(),)).fetchone()
        if existing:
            raise HTTPException(409, "Email đã được sử dụng")

        code = f"{secrets.randbelow(900000) + 100000}"
        salt = secrets.token_hex(16)
        password_hash = hash_password(body.password, salt)
        temp_data = json.dumps({"name": body.name, "password_hash": password_hash, "salt": salt}, ensure_ascii=False)
        now = int(time.time())
        expires_at = now + 600  # 10 minutes

        conn.execute("UPDATE verification_codes SET used=1 WHERE email=? AND purpose='register' AND used=0", (body.email.lower(),))
        conn.execute(
            "INSERT INTO verification_codes(email, code, purpose, temp_data_json, expires_at, created_at, used) VALUES(?,?,?,?,?,?,0)",
            (body.email.lower(), code, "register", temp_data, expires_at, now),
        )

    try:
        send_verification_email(body.email.lower(), code, "register")
    except Exception as exc:
        raise HTTPException(500, f"Không thể gửi mã xác thực tới email: {exc}")

    return {"status": "ok", "message": "Mã xác thực đã được gửi tới email của bạn", "email": body.email.lower()}


@app.post("/api/auth/register-verify", status_code=201)
def register_verify(body: RegisterVerify):
    now = int(time.time())
    with database() as conn:
        row = conn.execute(
            "SELECT * FROM verification_codes WHERE email=? AND purpose='register' AND code=? AND used=0 AND expires_at > ? ORDER BY id DESC LIMIT 1",
            (body.email.lower(), body.code, now),
        ).fetchone()
        if not row:
            raise HTTPException(400, "Mã xác thực không chính xác hoặc đã hết hạn")

        data = json.loads(row["temp_data_json"])
        try:
            uid = conn.execute(
                "INSERT INTO users(name,email,password_hash,salt,created_at) VALUES(?,?,?,?,?)",
                (data["name"], body.email.lower(), data["password_hash"], data["salt"], now),
            ).lastrowid
            conn.execute("UPDATE verification_codes SET used=1 WHERE id=?", (row["id"],))
            return session(conn, require_row(conn, "users", uid))
        except sqlite3.IntegrityError:
            raise HTTPException(409, "Email đã được sử dụng")


@app.post("/api/auth/forgot-password-request")
def forgot_password_request(body: ForgotPasswordRequest):
    with database() as conn:
        user = conn.execute("SELECT id, is_active FROM users WHERE email=?", (body.email.lower(),)).fetchone()
        if not user:
            raise HTTPException(404, "Email này chưa được đăng ký trong hệ thống")
        if not user["is_active"]:
            raise HTTPException(403, "Tài khoản này đã bị khóa")

        code = f"{secrets.randbelow(900000) + 100000}"
        now = int(time.time())
        expires_at = now + 600

        conn.execute("UPDATE verification_codes SET used=1 WHERE email=? AND purpose='forgot_password' AND used=0", (body.email.lower(),))
        conn.execute(
            "INSERT INTO verification_codes(email, code, purpose, temp_data_json, expires_at, created_at, used) VALUES(?,?,?,?,?,?,0)",
            (body.email.lower(), code, "forgot_password", "{}", expires_at, now),
        )

    try:
        send_verification_email(body.email.lower(), code, "forgot_password")
    except Exception as exc:
        raise HTTPException(500, f"Không thể gửi mã xác thực tới email: {exc}")

    return {"status": "ok", "message": "Mã xác thực đặt lại mật khẩu đã được gửi tới email của bạn"}


@app.post("/api/auth/forgot-password-verify")
def forgot_password_verify(body: ForgotPasswordVerify):
    now = int(time.time())
    with database() as conn:
        row = conn.execute(
            "SELECT * FROM verification_codes WHERE email=? AND purpose='forgot_password' AND code=? AND used=0 AND expires_at > ? ORDER BY id DESC LIMIT 1",
            (body.email.lower(), body.code, now),
        ).fetchone()
        if not row:
            raise HTTPException(400, "Mã xác thực không chính xác hoặc đã hết hạn")

        user = conn.execute("SELECT id FROM users WHERE email=?", (body.email.lower(),)).fetchone()
        if not user:
            raise HTTPException(404, "Không tìm thấy tài khoản người dùng")

        new_salt = secrets.token_hex(16)
        new_hash = hash_password(body.new_password, new_salt)
        conn.execute("UPDATE users SET password_hash=?, salt=?, version=version+1 WHERE id=?", (new_hash, new_salt, user["id"]))
        conn.execute("DELETE FROM sessions WHERE user_id=?", (user["id"],))
        conn.execute("UPDATE verification_codes SET used=1 WHERE id=?", (row["id"],))
        return {"status": "ok", "message": "Đặt lại mật khẩu thành công. Vui lòng đăng nhập với mật khẩu mới."}


def login_for_role(body: Login, role: str):
    with database() as conn:
        row = conn.execute("SELECT * FROM users WHERE email=?", (body.email.lower(),)).fetchone()
        # Perform the same expensive hash even when the email does not exist.
        candidate = hash_password(body.password, row["salt"] if row else "00" * 16)
        if row is None or not hmac.compare_digest(candidate, row["password_hash"]):
            raise HTTPException(401, "Email hoặc mật khẩu không đúng")
        if not row["is_active"]:
            raise HTTPException(403, "Tài khoản đã bị khóa")
        if row["role"] != role:
            message = "Tài khoản quản trị viên vui lòng đăng nhập tại /admin." if role == "student" else "Trang quản trị chỉ dành cho tài khoản admin. Học viên hãy đăng nhập ở trang chính."
            raise HTTPException(403, message)
        return session(conn, row)


@app.post("/api/auth/login")
def login(body: Login):
    return login_for_role(body, "student")


@app.post("/api/auth/admin-login")
def admin_login(body: Login):
    return login_for_role(body, "admin")


@app.get("/api/auth/student-session")
def student_session(user=Depends(current_user)):
    if user["role"] != "student":
        raise HTTPException(403, "Tài khoản quản trị viên vui lòng đăng nhập tại /admin.")
    from sepay_gateway import reconcile_recent_orders
    reconcile_recent_orders(user['id'])
    with database() as conn:
        refreshed = conn.execute('SELECT * FROM users WHERE id=?', (user['id'],)).fetchone()
    return public_user(refreshed)


@app.post("/api/auth/logout", status_code=204)
def logout(authorization: Annotated[str, Header()], user=Depends(current_user)):
    with database() as conn:
        conn.execute("DELETE FROM sessions WHERE token_hash=?", (hashlib.sha256(authorization[7:].encode()).hexdigest(),))


@app.get("/api/me")
def me(user=Depends(current_user)):
    return public_user(user)


@app.get("/api/admin/dashboard")
def dashboard(user=Depends(admin_user)):
    with database() as conn:
        totals: dict[str, Any] = row_to_dict(conn.execute("SELECT COUNT(*) users, COALESCE(SUM(is_active),0) active_users, COALESCE(SUM(role='admin'),0) admins FROM users").fetchone())
        for table in ("vocabulary", "exams", "results"):
            t_row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            totals[table] = t_row[0] if t_row else 0
        avg_row = conn.execute("SELECT COALESCE(ROUND(AVG(score),1),0) FROM results").fetchone()
        totals["average_score"] = avg_row[0] if avg_row else 0
        succ_row = conn.execute("SELECT COUNT(*) FROM ai_usage WHERE status='success'").fetchone()
        totals["ai_success"] = succ_row[0] if succ_row else 0
        err_row = conn.execute("SELECT COUNT(*) FROM ai_usage WHERE status='error'").fetchone()
        totals["ai_errors"] = err_row[0] if err_row else 0
        activity = [row_to_dict(row) for row in conn.execute("SELECT a.id,u.name,a.action,a.entity,a.entity_id,a.created_at FROM audit_logs a JOIN users u ON u.id=a.actor_id ORDER BY a.id DESC LIMIT 10")]
    return {"totals": totals, "recent_activity": activity}


@app.get("/api/admin/users")
def users(search: str = Query(default="", max_length=120), role: Literal["student", "admin"] | None = None,
          active: bool | None = None, user=Depends(admin_user)):
    query = "SELECT * FROM users WHERE (name LIKE ? OR email LIKE ?)"
    values: list[Any] = [f"%{search}%", f"%{search}%"]
    if role:
        query += " AND role=?"
        values.append(role)
    if active is not None:
        query += " AND is_active=?"
        values.append(int(active))
    with database() as conn:
        return [public_user(row) for row in conn.execute(query + " ORDER BY id DESC", values)]


@app.post("/api/admin/users", status_code=201)
def create_user_by_admin(body: AdminCreateUser, admin=Depends(admin_user)):
    email = body.email.strip().lower()
    with database() as conn:
        conn.execute("BEGIN IMMEDIATE")
        exists = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
        if exists:
            raise HTTPException(409, "Email đã được sử dụng")
        salt = secrets.token_hex(16)
        pw_hash = hash_password(body.password, salt)
        user_id = conn.execute(
            "INSERT INTO users(name, email, password_hash, salt, role, is_active, version, created_at) VALUES(?,?,?,?,?,?,1,?)",
            (body.name.strip(), email, pw_hash, salt, body.role, int(body.is_active), int(time.time()))
        ).lastrowid
        after = public_user(require_row(conn, "users", user_id))
        audit(conn, admin["id"], "create", "user", user_id, None, after)
    return after


@app.patch("/api/admin/users/{user_id}")
@app.put("/api/admin/users/{user_id}")
def update_user(user_id: int, body: UserUpdate, admin=Depends(admin_user)):
    if user_id == admin["id"] and (not body.is_active or body.role != "admin"):
        raise HTTPException(400, "Không thể tự khóa hoặc hạ quyền tài khoản đang dùng")
    with database() as conn:
        conn.execute("BEGIN IMMEDIATE")
        before = require_row(conn, "users", user_id)
        check_version(before, body.version)
        if before["role"] == "admin" and before["is_active"] and (not body.is_active or body.role != "admin"):
            admin_count = conn.execute("SELECT COUNT(*) FROM users WHERE role='admin' AND is_active=1").fetchone()
            if admin_count and admin_count[0] <= 1:
                raise HTTPException(409, "Phải giữ ít nhất một quản trị viên hoạt động")
        
        target_name = body.name.strip() if body.name else before["name"]
        target_email = body.email.strip().lower() if body.email else before["email"]
        if target_email != before["email"]:
            exists = conn.execute("SELECT id FROM users WHERE email=? AND id!=?", (target_email, user_id)).fetchone()
            if exists:
                raise HTTPException(409, "Email đã được sử dụng bởi tài khoản khác")

        new_hash = None
        new_salt = None
        if body.password and body.password.strip():
            pw = body.password.strip()
            if len(pw) < 8:
                raise HTTPException(422, "Mật khẩu mới phải có ít nhất 8 ký tự")
            new_salt = secrets.token_hex(16)
            new_hash = hash_password(pw, new_salt)

        if new_hash and new_salt:
            conn.execute(
                "UPDATE users SET name=?,email=?,role=?,is_active=?,password_hash=?,salt=?,version=version+1 WHERE id=?",
                (target_name, target_email, body.role, int(body.is_active), new_hash, new_salt, user_id)
            )
        else:
            conn.execute(
                "UPDATE users SET name=?,email=?,role=?,is_active=?,version=version+1 WHERE id=?",
                (target_name, target_email, body.role, int(body.is_active), user_id)
            )

        if not body.is_active or body.role != before["role"] or new_hash:
            conn.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
        after = public_user(require_row(conn, "users", user_id))
        audit(conn, admin["id"], "update", "user", user_id, public_user(before), after)
    return after


@app.delete("/api/admin/users/{user_id}")
def delete_user(user_id: int, admin=Depends(admin_user)):
    if user_id == admin["id"]:
        raise HTTPException(400, "Không thể tự xóa tài khoản quản trị viên đang đăng nhập")
    with database() as conn:
        conn.execute("BEGIN IMMEDIATE")
        before = require_row(conn, "users", user_id)
        if before["role"] == "admin" and before["is_active"]:
            admin_count = conn.execute("SELECT COUNT(*) FROM users WHERE role='admin' AND is_active=1 AND id!=?", (user_id,)).fetchone()
            if admin_count and admin_count[0] < 1:
                raise HTTPException(409, "Phải giữ lại ít nhất một quản trị viên hoạt động")
        
        # Clean up related tables
        for tbl in ["sessions", "profiles", "lesson_progress", "review_items",
                    "student_notebook", "student_reading_history", "student_ai_exams",
                    "exam_submissions", "results", "ai_usage", "personalized_practice"]:
            try:
                conn.execute(f"DELETE FROM {tbl} WHERE user_id=?", (user_id,))
            except sqlite3.OperationalError:
                pass
        conn.execute("DELETE FROM users WHERE id=?", (user_id,))
        audit(conn, admin["id"], "delete", "user", user_id, public_user(before), None)
    return {"status": "ok", "message": f"Đã xóa tài khoản {before['email']} thành công"}


@app.post("/api/admin/users/{user_id}/reset-password")
def admin_reset_user_password(user_id: int, body: AdminResetPassword, admin=Depends(admin_user)):
    with database() as conn:
        conn.execute("BEGIN IMMEDIATE")
        user = require_row(conn, "users", user_id)
        new_salt = secrets.token_hex(16)
        new_hash = hash_password(body.new_password, new_salt)
        conn.execute("UPDATE users SET password_hash=?,salt=?,version=version+1 WHERE id=?",
                     (new_hash, new_salt, user_id))
        conn.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
        after = public_user(require_row(conn, "users", user_id))
        audit(conn, admin["id"], "reset_password", "user", user_id, {"email": user["email"]}, {"email": user["email"]})
    return {"status": "ok", "message": f"Đặt lại mật khẩu cho {user['email']} thành công", "user": after}


@app.post("/api/admin/users/{user_id}/premium")
def admin_manage_user_premium(user_id: int, body: AdminUserPremiumAction, admin=Depends(admin_user)):
    """Admin grants or revokes HanziGo Premium directly for a student."""
    now = int(time.time())
    with database() as conn:
        conn.execute("BEGIN IMMEDIATE")
        before = require_row(conn, "users", user_id)
        if body.action == "grant":
            curr_until = before["premium_until"] or 0
            base_time = max(now, curr_until)
            duration_days = max(1, int(body.duration_days))
            new_until = base_time + duration_days * 86400
            freezes_to_add = max(0, int(body.added_freezes))
            conn.execute(
                "UPDATE users SET premium_until=?, streak_freezes=COALESCE(streak_freezes,0)+?, version=version+1 WHERE id=?",
                (new_until, freezes_to_add, user_id)
            )
            action_name = "grant_premium"
            msg = f"Đã cấp quyền HanziGo Premium ({duration_days} ngày) cho học viên thành công!"
        elif body.action == "revoke":
            conn.execute(
                "UPDATE users SET premium_until=0, version=version+1 WHERE id=?",
                (user_id,)
            )
            action_name = "revoke_premium"
            msg = "Đã gỡ quyền HanziGo Premium của học viên."
        else:
            raise HTTPException(400, "Hành động không hợp lệ.")

        after = require_row(conn, "users", user_id)
        audit(conn, admin["id"], action_name, "user", user_id, public_user(before), public_user(after))

    return {
        "success": True,
        "action": body.action,
        "message": msg,
        "user": public_user(after)
    }


@app.get("/api/admin/student-lessons")
def admin_student_lessons(user_id: int | None = None, stage: int | None = None, user=Depends(admin_user)):
    query = """
        SELECT p.user_id, p.lesson_id, p.stage, p.best_score, p.attempts, p.completed_at, p.updated_at,
               u.name, u.email
        FROM lesson_progress p
        JOIN users u ON p.user_id = u.id
        WHERE 1=1
    """
    params: list[Any] = []
    if user_id is not None:
        query += " AND p.user_id = ?"
        params.append(user_id)
    if stage is not None:
        query += " AND p.stage = ?"
        params.append(stage)
    query += " ORDER BY p.updated_at DESC LIMIT 200"
    with database() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


@app.get("/api/admin/student-reading")
def admin_student_reading(user_id: int | None = None, rating: str | None = None, user=Depends(admin_user)):
    query = """
        SELECT h.id, h.user_id, h.word_id, h.hanzi, h.pinyin, h.meaning,
               h.accuracy_percent, h.rating, h.spoken_text, h.errors_json,
               h.corrections_json, h.created_at, u.name, u.email
        FROM student_reading_history h
        JOIN users u ON h.user_id = u.id
        WHERE 1=1
    """
    params: list[Any] = []
    if user_id is not None:
        query += " AND h.user_id = ?"
        params.append(user_id)
    if rating:
        query += " AND h.rating = ?"
        params.append(rating)
    query += " ORDER BY h.created_at DESC LIMIT 200"
    with database() as conn:
        rows = conn.execute(query, params).fetchall()
        items = []
        for r in rows:
            d = dict(r)
            d["errors"] = json.loads(d.pop("errors_json", "[]") or "[]")
            d["corrections"] = json.loads(d.pop("corrections_json", "[]") or "[]")
            items.append(d)
        return items


@app.get("/api/admin/student-writing")
def admin_student_writing(user_id: int | None = None, kind: str | None = None, user=Depends(admin_user)):
    query = """
        SELECT r.id, r.user_id, r.exam_id, r.kind, r.content, r.score, r.original_score,
               r.feedback, r.graded_by, r.created_at, u.name, u.email
        FROM results r
        JOIN users u ON r.user_id = u.id
        WHERE r.kind IN ('handwriting', 'writing')
    """
    params: list[Any] = []
    if user_id is not None:
        query += " AND r.user_id = ?"
        params.append(user_id)
    if kind:
        query += " AND r.kind = ?"
        params.append(kind)
    query += " ORDER BY r.created_at DESC LIMIT 200"
    with database() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


@app.get("/api/admin/student-vocab")
def admin_student_vocab(user_id: int | None = None, user=Depends(admin_user)):
    with database() as conn:
        saved_query = """
            SELECT s.user_id, s.word_id, s.created_at, u.name, u.email,
                   v.hanzi, v.pinyin, v.meaning, v.hsk
            FROM saved_words s
            JOIN users u ON s.user_id = u.id
            JOIN vocabulary v ON s.word_id = v.id
            WHERE 1=1
        """
        params: list[Any] = []
        if user_id is not None:
            saved_query += " AND s.user_id = ?"
            params.append(user_id)
        saved_query += " ORDER BY s.created_at DESC LIMIT 100"
        try:
            saved = [dict(r) for r in conn.execute(saved_query, params).fetchall()]
        except Exception:
            saved = []

        top_query = """
            SELECT d.word_id, v.hanzi, v.pinyin, v.meaning, v.hsk,
                   SUM(d.lookup_count) AS total_lookups, COUNT(DISTINCT d.user_id) AS student_count
            FROM dictionary_history d
            JOIN vocabulary v ON d.word_id = v.id
            GROUP BY d.word_id
            ORDER BY total_lookups DESC LIMIT 50
        """
        try:
            top_looked_up = [dict(r) for r in conn.execute(top_query).fetchall()]
        except Exception:
            top_looked_up = []

        return {"saved_words": saved, "top_looked_up": top_looked_up}


@app.get("/api/admin/student-ai-exams")
def admin_student_ai_exams(
    user_id: int | None = None,
    hsk: int | None = None,
    status: str | None = None,
    search: str | None = None,
    user=Depends(admin_user)
):
    query = """
        SELECT e.id, e.user_id, e.title, e.content_type, e.hsk_level, e.topic,
               e.question_count, e.duration_minutes, e.status, e.score,
               e.submitted_at, e.created_at, u.name as student_name, u.email as student_email
        FROM student_ai_exams e
        JOIN users u ON e.user_id = u.id
        WHERE 1=1
    """
    params: list[Any] = []
    if user_id is not None:
        query += " AND e.user_id = ?"
        params.append(user_id)
    if hsk is not None:
        query += " AND e.hsk_level = ?"
        params.append(hsk)
    if status:
        query += " AND e.status = ?"
        params.append(status)
    if search:
        query += " AND (u.name LIKE ? OR u.email LIKE ? OR e.title LIKE ? OR e.topic LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s, s])
    query += " ORDER BY e.created_at DESC LIMIT 200"
    with database() as conn:
        try:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []


@app.get("/api/admin/student-ai-exams/{exam_id}")
def admin_student_ai_exam_detail(exam_id: int, user=Depends(admin_user)):
    with database() as conn:
        row = conn.execute("""
            SELECT e.*, u.name as student_name, u.email as student_email
            FROM student_ai_exams e
            JOIN users u ON e.user_id = u.id
            WHERE e.id = ?
        """, (exam_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Không tìm thấy đề thi AI")
        d = dict(row)
        d["questions"] = json.loads(d.pop("questions_json", "[]") or "[]")
        d["user_answers"] = json.loads(d.pop("user_answers_json", "{}") or "{}")
        d["ai_feedback"] = json.loads(d.pop("ai_feedback_json", "{}") or "{}")
        return d


@app.delete("/api/admin/student-ai-exams/{exam_id}")
def admin_delete_student_ai_exam(exam_id: int, user=Depends(admin_user)):
    with database() as conn:
        conn.execute("BEGIN IMMEDIATE")
        before = conn.execute("SELECT * FROM student_ai_exams WHERE id = ?", (exam_id,)).fetchone()
        if not before:
            raise HTTPException(404, "Không tìm thấy đề thi AI")
        conn.execute("DELETE FROM student_ai_exams WHERE id = ?", (exam_id,))
        audit(conn, user["id"], "delete", "student_ai_exam", exam_id, dict(before), None)
    return {"status": "ok", "message": f"Đã xóa đề thi AI #{exam_id}"}




def word_json(row: Any) -> dict[str, Any]:
    item = row_to_dict(row)
    item["strokes"] = json.loads(item.pop("strokes_json", "[]") or "[]")
    item.update(stroke_metadata(item["hanzi"]))
    return item


@app.get("/api/vocabulary")
def vocabulary(search: str = Query(default="", max_length=120), hsk: int | None = Query(default=None, ge=1, le=6)):
    query = "SELECT * FROM vocabulary WHERE (hanzi LIKE ? OR pinyin LIKE ? OR meaning LIKE ?)"
    values: list[Any] = [f"%{search}%"] * 3
    if hsk:
        query += " AND hsk=?"
        values.append(hsk)
    with database() as conn:
        return [word_json(row) for row in conn.execute(query + " ORDER BY hsk,id", values)]


@app.post("/api/me/dictionary-history/{word_id}", status_code=201)
def record_dictionary_lookup(word_id: int, body: DictionaryLookup, user=Depends(current_user)):
    now = int(time.time())
    with database() as conn:
        require_row(conn, "vocabulary", word_id)
        conn.execute(
            """INSERT INTO dictionary_history(user_id,word_id,query,last_looked_at)
               VALUES(?,?,?,?)
               ON CONFLICT(user_id,word_id) DO UPDATE SET
                 query=excluded.query, lookup_count=lookup_count+1,
                 last_looked_at=excluded.last_looked_at""",
            (user["id"], word_id, body.query, now),
        )
        row = conn.execute(
            """SELECT h.*,v.hanzi,v.pinyin,v.meaning,v.hsk,v.example,v.audio_url,v.strokes_json
               FROM dictionary_history h JOIN vocabulary v ON v.id=h.word_id
               WHERE h.user_id=? AND h.word_id=?""",
            (user["id"], word_id),
        ).fetchone()
    return word_json(row)


@app.get("/api/me/dictionary-history")
def dictionary_history(user=Depends(current_user)):
    with database() as conn:
        rows = conn.execute(
            """SELECT h.*,v.hanzi,v.pinyin,v.meaning,v.hsk,v.example,v.audio_url,v.strokes_json
               FROM dictionary_history h JOIN vocabulary v ON v.id=h.word_id
               WHERE h.user_id=? ORDER BY h.last_looked_at DESC""",
            (user["id"],),
        ).fetchall()
    items = []
    for row in rows:
        item = dict(row)
        item["strokes"] = json.loads(item.pop("strokes_json"))
        items.append(item)
    return items


@app.get("/api/admin/vocabulary")
def admin_vocabulary(search: str = Query(default="", max_length=120), hsk: int | None = Query(default=None, ge=1, le=6), user=Depends(admin_user)):
    return vocabulary(search, hsk)


def save_word(body, admin, word_id=None):
    data = body.model_dump(exclude={"version"})
    data["strokes_json"] = json.dumps(data.pop("strokes"), ensure_ascii=False)
    try:
        with database() as conn:
            conn.execute("BEGIN IMMEDIATE")
            before = None
            if word_id is not None:
                before = require_row(conn, "vocabulary", word_id)
                check_version(before, body.version)
                conn.execute("UPDATE vocabulary SET hanzi=?,pinyin=?,meaning=?,hsk=?,example=?,audio_url=?,strokes_json=?,version=version+1 WHERE id=?", (*data.values(), word_id))
            else:
                word_id = conn.execute("INSERT INTO vocabulary(hanzi,pinyin,meaning,hsk,example,audio_url,strokes_json) VALUES(?,?,?,?,?,?,?)", tuple(data.values())).lastrowid
            from vocabulary_catalog import refresh_search
            refresh_search(conn, word_id)
            after = word_json(require_row(conn, "vocabulary", word_id))
            audit(conn, admin["id"], "update" if before else "create", "vocabulary", word_id,
                  word_json(before) if before else None, after)
            return after
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Chữ Hán đã tồn tại")


@app.post("/api/admin/vocabulary", status_code=201)
def add_word(body: Word, admin=Depends(admin_user)):
    return save_word(body, admin)


@app.put("/api/admin/vocabulary/{word_id}")
def edit_word(word_id: int, body: WordUpdate, admin=Depends(admin_user)):
    return save_word(body, admin, word_id)


@app.delete("/api/admin/vocabulary/{word_id}", status_code=204)
def delete_word(word_id: int, version: int = Query(ge=1), admin=Depends(admin_user)):
    try:
        with database() as conn:
            conn.execute("BEGIN IMMEDIATE")
            before = require_row(conn, "vocabulary", word_id)
            check_version(before, version)
            conn.execute("DELETE FROM vocabulary WHERE id=?", (word_id,))
            audit(conn, admin["id"], "delete", "vocabulary", word_id, word_json(before))
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Từ đang được dùng trong đề thi, lịch sử hoặc sổ tay. Hãy gỡ liên kết trước khi xóa.")


def exam_json(row, learner=False):
    item = dict(row)
    item["questions"] = json.loads(item.pop("questions_json"))
    if learner:
        for q in item["questions"]:
            for key in ("answer", "explanation", "transcript"):
                q.pop(key, None)
        for q in item["questions"]:
            if "audio_url" not in q:
                q["audio_url"] = ""
    return item


@app.get("/api/admin/exams")
def admin_exams(hsk: int | None = Query(default=None, ge=1, le=6), user=Depends(admin_user)):
    with database() as conn:
        rows = conn.execute("SELECT * FROM exams" + (" WHERE hsk=?" if hsk else "") + " ORDER BY id DESC", (hsk,) if hsk else ())
        return [exam_json(row) for row in rows]


@app.get("/api/exams")
def learner_exams(hsk: int | None = Query(default=None, ge=1, le=9), user=Depends(current_user)):
    if hsk and hsk > 6:
        from advanced_hsk import public_exams
        return public_exams(hsk, user)
    with database() as conn:
        rows = conn.execute("SELECT * FROM exams WHERE status='published'" + (" AND hsk=?" if hsk else "") + " ORDER BY hsk,id", (hsk,) if hsk else ()).fetchall()
        # Ensure comprehensive exams exist if not yet seeded
        has_comp = any("Toàn diện" in (r["title"] if hasattr(r, "__getitem__") else "") for r in rows)
        if not has_comp and "unittest" not in sys.modules and not os.getenv("TESTING"):
            from database import init_comprehensive_exams
            init_comprehensive_exams(conn)
            rows = conn.execute("SELECT * FROM exams WHERE status='published'" + (" AND hsk=?" if hsk else "") + " ORDER BY hsk,id", (hsk,) if hsk else ()).fetchall()
        return [exam_json(row, learner=True) for row in rows]




def save_exam(body, admin, exam_id=None):
    questions = [q.model_dump() for q in body.questions]
    with database() as conn:
        conn.execute("BEGIN IMMEDIATE")
        for q in questions:
            if q["word_id"] is not None:
                linked_word = require_row(conn, "vocabulary", q["word_id"])
                if (q.get("question_type") == "hanzi_canvas"
                        and linked_word["hanzi"] != q["answer"]):
                    raise HTTPException(
                        422, "ID từ liên quan không khớp chữ Hán đáp án Canvas")
            if q.get("question_type") == "hanzi_canvas":
                word = conn.execute(
                    "SELECT id,strokes_json FROM vocabulary WHERE hanzi=?",
                    (q["answer"],),
                ).fetchone()
                if word is None or not json.loads(word["strokes_json"]):
                    raise HTTPException(
                        422, "Chữ Hán Canvas chưa có dữ liệu nét chuẩn")
                # Link automatically so the referenced stroke data cannot be deleted.
                q["word_id"] = word["id"]
        values = (body.title, body.hsk, body.status, body.duration_minutes, json.dumps(questions, ensure_ascii=False))
        before = None
        if exam_id is not None:
            before = require_row(conn, "exams", exam_id)
            check_version(before, body.version)
            conn.execute("UPDATE exams SET title=?,hsk=?,status=?,duration_minutes=?,questions_json=?,version=version+1 WHERE id=?", (*values, exam_id))
            conn.execute("DELETE FROM exam_words WHERE exam_id=?", (exam_id,))
        else:
            exam_id = conn.execute("INSERT INTO exams(title,hsk,status,duration_minutes,questions_json) VALUES(?,?,?,?,?)", values).lastrowid
        conn.executemany("INSERT INTO exam_words VALUES(?,?)", [(exam_id, wid) for wid in {q["word_id"] for q in questions if q["word_id"] is not None}])
        after = exam_json(require_row(conn, "exams", exam_id))
        audit(conn, admin["id"], "update" if before else "create", "exam", exam_id, exam_json(before) if before else None, after)
        return after


@app.post("/api/admin/exams", status_code=201)
def add_exam(body: Exam, admin=Depends(admin_user)):
    return save_exam(body, admin)


@app.put("/api/admin/exams/{exam_id}")
def edit_exam(exam_id: int, body: ExamUpdate, admin=Depends(admin_user)):
    return save_exam(body, admin, exam_id)


@app.delete("/api/admin/exams/{exam_id}", status_code=204)
def delete_exam(exam_id: int, version: int = Query(ge=1), admin=Depends(admin_user)):
    try:
        with database() as conn:
            conn.execute("BEGIN IMMEDIATE")
            before = require_row(conn, "exams", exam_id)
            check_version(before, version)
            conn.execute("DELETE FROM exams WHERE id=?", (exam_id,))
            audit(conn, admin["id"], "delete", "exam", exam_id, exam_json(before))
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Đề đã có kết quả. Hãy chuyển sang trạng thái ẩn để giữ lịch sử.")


def _exam_answer_json(value):
    return value if isinstance(value, str) else value.model_dump()


def normalize_answer_text(ans: Any) -> str:
    if ans is None:
        return ""
    text = str(ans).strip().lower()
    text = re.sub(r'^[a-d0-9][\.\)\:\-\s]+', '', text).strip()
    return text


def is_answer_correct(submitted: Any, correct: Any, options: list[str] | None = None) -> bool:
    sub_raw = str(submitted or "").strip()
    cor_raw = str(correct or "").strip()
    if not sub_raw or not cor_raw:
        return False
    if sub_raw.lower() == cor_raw.lower():
        return True
    sub_norm = normalize_answer_text(sub_raw)
    cor_norm = normalize_answer_text(cor_raw)
    if sub_norm and cor_norm and sub_norm == cor_norm:
        return True
    if options and isinstance(options, list):
        letters = ["a", "b", "c", "d", "e", "f"]
        sub_low = sub_raw.lower()
        cor_low = cor_raw.lower()
        if sub_low in letters:
            idx = letters.index(sub_low)
            if 0 <= idx < len(options):
                opt_norm = normalize_answer_text(options[idx])
                if opt_norm == cor_norm or options[idx].strip().lower() == cor_low:
                    return True
        if cor_low in letters:
            idx = letters.index(cor_low)
            if 0 <= idx < len(options):
                opt_norm = normalize_answer_text(options[idx])
                if opt_norm == sub_norm or options[idx].strip().lower() == sub_low:
                    return True
    return False


def grade_objective_exam(questions: list[dict], answers: dict[str, Any]) -> dict[str, Any]:
    total_weight = 0.0
    weighted_score = 0.0
    review_items = []
    section_totals: dict[str, list[float]] = {}
    correct_count = 0

    for q in questions:
        qid = q["id"]
        section = q.get("section", "exam")
        weight = float(q.get("weight", 1.0))
        total_weight += weight
        sub_ans = answers.get(str(qid), answers.get(qid, ""))
        cor_ans = q.get("answer", "")
        options = q.get("options")
        transcript = (q.get("transcript") or "").strip()
        explanation = (q.get("explanation") or "").strip()

        correct = is_answer_correct(sub_ans, cor_ans, options)
        q_score = 100.0 if correct else 0.0
        weighted_score += q_score * weight
        if correct:
            correct_count += 1

        if section not in section_totals:
            section_totals[section] = [0.0, 0.0]
        section_totals[section][0] += q_score * weight
        section_totals[section][1] += weight

        parts = []
        if correct:
            parts.append(f"Chính xác! Đáp án đúng: {cor_ans}.")
        else:
            parts.append(f"Chưa chính xác. Đáp án đúng: {cor_ans}.")
        if transcript:
            parts.append(f"Nội dung nghe: \"{transcript}\".")
        if explanation:
            parts.append(f"Giải thích: {explanation}")

        review_items.append({
            "id": str(qid),
            "explanation": " ".join(parts).strip()
        })

    overall_score = round(weighted_score / total_weight, 2) if total_weight > 0 else 0.0
    section_scores = {
        sec: round(tot[0] / tot[1], 2) if tot[1] > 0 else 0.0
        for sec, tot in section_totals.items()
    }
    feedback = f"Bạn trả lời đúng {correct_count}/{len(questions)} câu ({overall_score}/100 điểm)."

    return {
        "score": overall_score,
        "feedback": feedback,
        "review_items": review_items,
        "section_scores": section_scores,
        "graded_by": "automatic",
    }


def _legacy_exam_grade(exam, questions, answers, user_id, grader):
    sections = {q["section"] for q in questions}
    ai_kind = next(iter(sections)) if len(sections) == 1 else "exam"
    grading_content = json.dumps({
        "exam_title": exam["title"],
        "questions": [{
            "id": q["id"], "section": q["section"], "prompt": q["prompt"],
            "options": q["options"], "answer": q["answer"],
            "submitted_answer": answers.get(str(q["id"]), answers.get(q["id"], "")),
            "transcript": q.get("transcript", ""),
            "explanation": q.get("explanation", ""),
        } for q in questions]
    }, ensure_ascii=False)
    grade_function = ({"reading": grader, "listening": grade_listening_exam}
                      .get(ai_kind, grade_comprehensive_exam))
    try:
        res = grade_function(user_id, grading_content)
        if "graded_by" not in res:
            res["graded_by"] = "ai"
        return res
    except Exception as exc:
        logging.warning("AI grading failed for exam %s (%s): %s; using deterministic fallback.",
                        exam.get("id"), ai_kind, exc)
        return grade_objective_exam(questions, answers)


def fetch_or_get_stroke_guide(char: str) -> dict[str, Any]:
    if not char:
        raise HTTPException(400, "Vui lòng nhập chữ cần xem nét")
    target = char.strip()[0]
    pinyin = ""
    meaning = ""
    hsk = 0
    strokes = []

    with database() as conn:
        word = conn.execute("SELECT * FROM vocabulary WHERE hanzi=?", (target,)).fetchone()
        if word:
            pinyin = word["pinyin"]
            meaning = word["meaning"]
            hsk = word["hsk"]
            raw_strokes = json.loads(word["strokes_json"] or "[]")
            if raw_strokes:
                strokes = raw_strokes

    if not strokes:
        char_code = f"{ord(target):04x}"
        cache_path = Path(__file__).parent / "data" / "stroke_data" / f"{char_code}.json"
        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                    strokes = cached_data.get("strokes", [])
            except Exception:
                pass

        if not strokes:
            try:
                import urllib.parse
                import urllib.request
                url = f"https://cdn.jsdelivr.net/npm/hanzi-writer-data@latest/{urllib.parse.quote(target)}.json"
                req = urllib.request.Request(url, headers={"User-Agent": "HanziGo/1.0"})
                with urllib.request.urlopen(req, timeout=4) as resp:
                    hw_data = json.loads(resp.read().decode("utf-8"))
                    medians = hw_data.get("medians", [])
                    for s in medians:
                        strokes.append([{"x": round(pt[0]), "y": round(900 - pt[1])} for pt in s])

                if strokes:
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(cache_path, "w", encoding="utf-8") as f:
                        json.dump({"char": target, "strokes": strokes}, f, ensure_ascii=False)

                    with database() as conn:
                        conn.execute("UPDATE vocabulary SET strokes_json=? WHERE hanzi=?", (json.dumps(strokes), target))
            except Exception:
                pass

    return {
        "char": target,
        "pinyin": pinyin,
        "meaning": meaning,
        "hsk": hsk,
        "total_strokes": len(strokes),
        "strokes": strokes,
    }


def _grade_exam_canvas(target: str, strokes: list[list[dict]]):
    guide = fetch_or_get_stroke_guide(target)
    standard = guide.get("strokes", [])
    if not standard:
        raise HTTPException(422, "Chữ Hán chưa có dữ liệu nét chuẩn")
    return compare_handwriting_strokes(standard, strokes)


@app.post("/api/test-writing/grade-canvas",
          response_model=HandwritingGradeResponse)
def grade_test_canvas(body: ExamCanvasGradeRequest,
                      user=Depends(current_user)):
    strokes = [[point.model_dump() for point in stroke]
               for stroke in body.strokes]
    return _grade_exam_canvas(body.target, strokes)


@app.post("/api/test-writing/grade-essay",
          response_model=EssayGradeResponse)
def grade_test_essay(body: EssayGradeRequest, user=Depends(current_user)):
    return grade_essay_with_ai(
        user["id"], body.prompt, body.rubric, body.text,
        gemini_essay_provider)


def _submit_extended_exam(exam_id, exam, questions, body, user, grader):
    answers = {key: _exam_answer_json(value)
               for key, value in body.answers.items()}
    legacy_questions = [q for q in questions if q.get("question_type") not in ("hanzi_canvas", "essay")]
    special_questions = [q for q in questions if q.get("question_type") in ("hanzi_canvas", "essay")]
    question_scores = {}
    ai_review_items = []
    feedback_parts = []
    used_ai = False

    if legacy_questions:
        if any(not isinstance(answers[q["id"]], str)
               for q in legacy_questions):
            raise HTTPException(422, "Câu hỏi cũ cần đáp án dạng văn bản")
        legacy_grade = _legacy_exam_grade(
            exam, legacy_questions, answers, user["id"], grader)
        legacy_source = legacy_grade.get("graded_by", "ai")
        if legacy_source == "ai":
            used_ai = True
        if legacy_grade.get("feedback"):
            feedback_parts.append(legacy_grade["feedback"])
        ai_review_items.extend(legacy_grade.get("review_items", []))
        for question in legacy_questions:
            question_scores[question["id"]] = {
                "score": round(float(legacy_grade["score"]), 2),
                "feedback": legacy_grade.get("feedback", ""),
                "graded_by": legacy_source,
            }

    for question in special_questions:
        answer = answers[question["id"]]
        question_type = question["question_type"]
        if (not isinstance(answer, dict)
                or answer.get("kind") != question_type):
            raise HTTPException(
                422, f"Câu {question['id']} cần đáp án loại {question_type}")
        if question_type == "hanzi_canvas":
            grade = _grade_exam_canvas(question["answer"], answer["strokes"])
            source = "automatic"
        elif question_type == "essay":
            grade = grade_essay_with_ai(
                user["id"], question["prompt"], question["answer"],
                answer["text"], gemini_essay_provider)
            source = "ai"
            used_ai = True
        else:
            raise HTTPException(422, "Loại câu hỏi writing không hỗ trợ")
        question_scores[question["id"]] = {
            "score": grade["score"],
            "feedback": grade["feedback"],
            "graded_by": source,
            "details": grade.get("details", {}),
        }
        feedback_parts.append(f"Câu {question['id']}: {grade['feedback']}")
        ai_review_items.append({
            "id": question["id"], "explanation": grade["feedback"]})

    total_weight = sum(float(q.get("weight", 1)) for q in questions)
    score = round(sum(
        question_scores[q["id"]]["score"] * float(q.get("weight", 1))
        for q in questions) / total_weight, 2)
    section_totals = {}
    for question in questions:
        section = question["section"]
        weight = float(question.get("weight", 1))
        weighted, weights = section_totals.get(section, (0.0, 0.0))
        section_totals[section] = (
            weighted + question_scores[question["id"]]["score"] * weight,
            weights + weight,
        )
    section_scores = {
        section: round(weighted / weights, 2)
        for section, (weighted, weights) in section_totals.items()
    }
    feedback = " ".join(feedback_parts)
    graded_by = "ai" if used_ai else "automatic"
    snapshot = json.dumps({
        "exam_title": exam["title"], "exam_version": exam["version"],
        "questions": questions, "answers": answers,
        "ai_review_items": ai_review_items,
        "section_scores": section_scores,
        "question_scores": question_scores,
    }, ensure_ascii=False)
    with database() as conn:
        conn.execute("BEGIN IMMEDIATE")
        current = require_row(conn, "exams", exam_id)
        if current["status"] != "published":
            raise HTTPException(404, "Đề thi chưa được phát hành")
        check_version(current, body.version)
        rid = conn.execute(
            """INSERT INTO results(
                   user_id,exam_id,kind,content,score,original_score,feedback,
                   graded_by,created_at
               ) VALUES(?,?,'exam',?,?,?,?,?,?)""",
            (user["id"], exam_id, snapshot, score, score, feedback,
             graded_by, int(time.time())),
        ).lastrowid
        res_data = require_row(conn, "results", rid)
        if score >= 100:
            try:
                from premium_service import create_ai_100_score_voucher
                res_data["reward_voucher"] = create_ai_100_score_voucher(conn, user["id"])
            except Exception as exc:
                logging.warning("Failed to auto-create AI voucher on extended exam: %s", exc)
        return res_data


@app.post("/api/exams/{exam_id}/submit", status_code=201)
def submit(exam_id: int, body: Submission, user=Depends(current_user), grader=Depends(get_exam_ai_grader)):
    if exam_id < 0:
        from advanced_hsk import submit as submit_advanced
        return submit_advanced(exam_id, body, user)
    with database() as conn:
        exam = require_row(conn, "exams", exam_id)
        if exam["status"] != "published":
            raise HTTPException(404, "Đề thi chưa được phát hành")
        check_version(exam, body.version)
        questions = json.loads(exam["questions_json"])
        if any(q.get("question_type") for q in questions):
            if set(body.answers) != {q["id"] for q in questions}:
                raise HTTPException(
                    422, "Cần nộp đúng danh sách mã câu hỏi của đề")
            return _submit_extended_exam(
                exam_id, exam, questions, body, user, grader)
        if any(not isinstance(value, str) for value in body.answers.values()):
            raise HTTPException(422, "Câu hỏi cũ cần đáp án dạng văn bản")
        if set(body.answers) != {q["id"] for q in questions}:
            raise HTTPException(422, "Cần nộp đúng danh sách mã câu hỏi của đề")

    sections = {q["section"] for q in questions}
    ai_kind = next(iter(sections)) if len(sections) == 1 else "exam"
    if sections and sections <= {"reading", "listening", "writing"}:
        grading_content = json.dumps({
            "exam_title": exam["title"],
            "questions": [{
                "id": q["id"], "section": q["section"], "prompt": q["prompt"],
                "options": q["options"], "answer": q["answer"],
                "submitted_answer": body.answers[q["id"]],
                "transcript": q.get("transcript", ""),
                "explanation": q.get("explanation", ""),
            } for q in questions]
        }, ensure_ascii=False)
        grade_function = ({"reading": grader, "listening": grade_listening_exam}
                          .get(ai_kind, grade_comprehensive_exam))
        try:
            grade = grade_function(user["id"], grading_content)
            score, feedback, graded_by = grade["score"], grade["feedback"], grade.get("graded_by", "ai")
            ai_review_items = grade.get("review_items", [])
            section_scores = grade.get("section_scores", {section: score for section in sections})
        except Exception as exc:
            logging.warning("AI grading failed in submit for exam %s: %s; falling back to objective grading.",
                            exam_id, exc)
            fallback = grade_objective_exam(questions, body.answers)
            score, feedback, graded_by = fallback["score"], fallback["feedback"], "automatic"
            ai_review_items = fallback.get("review_items", [])
            section_scores = fallback.get("section_scores", {section: score for section in sections})
    else:
        fallback = grade_objective_exam(questions, body.answers)
        score, feedback, graded_by = fallback["score"], fallback["feedback"], "automatic"
        ai_review_items = fallback.get("review_items", [])
        section_scores = fallback.get("section_scores", {})

    snapshot = json.dumps({"exam_title": exam["title"], "exam_version": exam["version"],
                           "questions": questions, "answers": body.answers,
                           "ai_review_items": ai_review_items,
                           "section_scores": section_scores}, ensure_ascii=False)
    with database() as conn:
        conn.execute("BEGIN IMMEDIATE")
        current = require_row(conn, "exams", exam_id)
        if current["status"] != "published":
            raise HTTPException(404, "Đề thi chưa được phát hành")
        check_version(current, body.version)
        rid = conn.execute("INSERT INTO results(user_id,exam_id,kind,content,score,original_score,feedback,graded_by,created_at) VALUES(?,?,'exam',?,?,?,?,?,?)",
                           (user["id"], exam_id, snapshot, score, score, feedback, graded_by, int(time.time()))).lastrowid
        res_data = require_row(conn, "results", rid)
        if score >= 100:
            try:
                from premium_service import create_ai_100_score_voucher
                res_data["reward_voucher"] = create_ai_100_score_voucher(conn, user["id"])
            except Exception as exc:
                logging.warning("Failed to auto-create AI voucher on submit: %s", exc)
        return res_data


@app.get("/api/admin/ai-config")
def get_ai_config(user=Depends(admin_user)):
    from support_chat import DEFAULT_CHAT_SYSTEM_PROMPT, DEFAULT_OFF_TOPIC_DECLINE_MESSAGE
    with database() as conn:
        result = require_row(conn, "ai_config", 1)
        since = int(time.time()) - 86400
        usage = conn.execute(
            "SELECT status,COUNT(*) AS count FROM ai_usage WHERE created_at>=? GROUP BY status", (since,)).fetchall()
        result["usage_24h"] = {row["status"]: row["count"] for row in usage}
        result["recent_usage"] = [row_to_dict(row) for row in conn.execute(
            """SELECT a.module,a.status,a.created_at,COALESCE(u.name,'Khách / hệ thống') AS name
               FROM ai_usage a LEFT JOIN users u ON u.id=a.user_id ORDER BY a.id DESC LIMIT 8""").fetchall()]
        chat_stats = conn.execute(
            "SELECT COUNT(DISTINCT thread_id) AS threads, COUNT(*) AS messages FROM chat_messages"
        ).fetchone()
        result["chat_stats"] = {
            "threads": chat_stats["threads"] if chat_stats else 0,
            "messages": chat_stats["messages"] if chat_stats else 0
        }
    result["model"] = configured_model(result)
    result["key_configured"] = bool(configured_api_key())
    result["fallback_model"] = os.getenv("GEMINI_FALLBACK_MODEL", "").strip()
    result["ready"] = bool(result["enabled"] and result["key_configured"] and result["model"])
    result["chat_prompt"] = (result.get("chat_prompt") or "").strip() or DEFAULT_CHAT_SYSTEM_PROMPT
    result["chat_decline_message"] = (result.get("chat_decline_message") or "").strip() or DEFAULT_OFF_TOPIC_DECLINE_MESSAGE
    result["chat_strict_mode"] = bool(result.get("chat_strict_mode", 1)) if result.get("chat_strict_mode") is not None else True
    return result


@app.put("/api/admin/ai-config")
def update_ai_config(body: AIConfig, admin=Depends(admin_user)):
    if body.enabled and (not configured_api_key() or body.model == "configure-your-model"):
        raise HTTPException(422, "Cần đặt GEMINI_API_KEY trên máy chủ và chọn model trước khi bật AI")
    with database() as conn:
        conn.execute("BEGIN IMMEDIATE")
        before = require_row(conn, "ai_config", 1)
        check_version(before, body.version)
        chat_prompt = body.chat_prompt if body.chat_prompt is not None else before.get("chat_prompt", "")
        chat_decline = body.chat_decline_message if body.chat_decline_message is not None else before.get("chat_decline_message", "")
        chat_strict = int(body.chat_strict_mode) if body.chat_strict_mode is not None else int(before.get("chat_strict_mode", 1))
        conn.execute("""UPDATE ai_config SET 
                        model=?,system_prompt=?,temperature=?,max_tokens=?,enabled=?,
                        chat_prompt=?,chat_decline_message=?,chat_strict_mode=?,
                        version=version+1 WHERE id=1""",
                     (body.model, body.system_prompt, body.temperature, body.max_tokens, int(body.enabled),
                      chat_prompt, chat_decline, chat_strict))
        audit(conn, admin["id"], "update", "ai_config", 1, before, require_row(conn, "ai_config", 1))
    return get_ai_config(admin)


@app.post("/api/admin/ai-config/test")
def test_ai_connection(admin=Depends(admin_user)):
    from services import ai_settings, record_ai_usage
    from ai_provider import gemini_grade
    settings = ai_settings()
    try:
        gemini_grade(settings, "Bài kiểm tra kết nối: 你好。")
    except Exception as error:
        record_ai_usage(admin["id"], "connection_test", "error")
        with database() as conn:
            audit(conn, admin["id"], "connection_test", "ai_config", 1, None,
                  {"model": settings["model"], "status": "error"})
        raise ai_http_error(error, "Không nhận được phản hồi AI hợp lệ. Kiểm tra model, khóa và hạn mức trên máy chủ.") from None
    record_ai_usage(admin["id"], "connection_test", "success")
    with database() as conn:
        audit(conn, admin["id"], "connection_test", "ai_config", 1, None,
              {"model": settings["model"], "status": "success"})
    return {"status": "ok", "message": "Đã nhận phản hồi hợp lệ từ Trợ lý AI. Không tạo điểm học viên."}


@app.get("/api/admin/results")
def admin_results(user_id: int | None = None, below: float | None = Query(default=None, ge=0, le=100), user=Depends(admin_user)):
    query = "SELECT r.*,u.name,u.email FROM results r JOIN users u ON r.user_id=u.id WHERE 1=1"
    params = []
    if user_id is not None:
        query += " AND r.user_id=?"
        params.append(user_id)
    if below is not None:
        query += " AND r.score<?"
        params.append(below)
    with database() as conn:
        return [dict(row) for row in conn.execute(query + " ORDER BY r.id DESC", params)]


@app.post("/api/writing/submit", status_code=201)
def submit_writing(body: WritingSubmission, user=Depends(current_user)):
    payload = json.dumps({"content": body.content}, ensure_ascii=False)
    return grade_with_ai(user["id"], "writing", payload, gemini_provider)


@app.post("/api/translation/analyze", response_model=GrammarAnalysisResponse)
def analyze_translation(body: GrammarAnalysisRequest,
                        user=Depends(current_user)):
    """Correct one Chinese sentence and assess its optional intended context."""
    return analyze_grammar_with_ai(
        user["id"], body.sentence, body.context, gemini_grammar_provider)


def grade_handwriting_submission(body: HandwritingSubmission, user_id: int):
    guide = fetch_or_get_stroke_guide(body.target)
    standard = guide.get("strokes", [])
    if not standard:
        raise HTTPException(422, "Chữ Hán chưa có dữ liệu nét chuẩn")
    submitted = [[point.model_dump() for point in stroke] for stroke in body.strokes]
    return grade_handwriting_offline(user_id, body.target, standard, submitted)


@app.post("/api/handwriting/submit", status_code=201,
          response_model=HandwritingGradeResponse)
def submit_handwriting(body: HandwritingSubmission, user=Depends(current_user)):
    grade, _ = grade_handwriting_submission(body, user["id"])
    return grade


@app.get("/api/handwriting/stroke-guide")
def handwriting_stroke_guide(char: str = Query(..., max_length=20)):
    """Fetch stroke-by-stroke guide for any Hanzi with HSK info and ordered stroke coordinates."""
    return fetch_or_get_stroke_guide(char)


@app.get("/api/me/handwriting-retry-items",
         response_model=list[HandwritingRetryItem])
def handwriting_retry_items(user=Depends(current_user)):
    """List weak characters by their latest attempt, lowest score first."""
    with database() as conn:
        rows = conn.execute(
            """SELECT id,kind,content,score,created_at FROM results
               WHERE user_id=? AND kind IN ('handwriting','exam')
               ORDER BY created_at,id""",
            (user["id"],),
        ).fetchall()
    return build_handwriting_retry_items(rows)


@app.post(
    "/api/handwriting/recognize",
    response_model=HandwritingRecognitionResponse,
)
def recognize_handwriting(body: HandwritingRecognition, user=Depends(current_user)):
    """Recognize Canvas strokes and return ranked, vocabulary-enriched matches."""
    strokes = [[point.model_dump() for point in stroke] for stroke in body.strokes]
    return recognize_handwriting_with_ai(
        user["id"], strokes, gemini_handwriting_recognition_provider)


@app.get("/api/me/review-items")
def review_items(kind: str = Query(default="writing"),
                 below: float = Query(default=80, gt=0, le=100),
                 user=Depends(current_user)):
    with database() as conn:
        if kind == "reading":
            try:
                rows = conn.execute(
                    """SELECT id, word_id, hanzi, pinyin, meaning, accuracy_percent, rating, spoken_text, created_at
                       FROM student_reading_history
                       WHERE user_id=? AND accuracy_percent<?
                       ORDER BY created_at DESC""",
                    (user["id"], below),
                ).fetchall()
                return [
                    {
                        "id": r["id"],
                        "kind": "reading",
                        "score": r["accuracy_percent"],
                        "title": r["hanzi"],
                        "subtitle": f"{r['pinyin']} · {r['meaning'] or ''}",
                        "spoken_text": r["spoken_text"],
                        "rating": r["rating"],
                        "created_at": r["created_at"],
                    }
                    for r in rows
                ]
            except Exception:
                return []

        if kind == "exam":
            try:
                rows = conn.execute(
                    """SELECT id, title, hsk_level, question_count, score, submitted_at, created_at
                       FROM student_ai_exams
                       WHERE user_id=? AND status='completed' AND score<?
                       ORDER BY created_at DESC""",
                    (user["id"], below),
                ).fetchall()
                return [
                    {
                        "id": r["id"],
                        "kind": "exam",
                        "score": r["score"],
                        "title": r["title"],
                        "subtitle": f"HSK {r['hsk_level'] or 'Tổng hợp'} · {r['question_count']} câu",
                        "created_at": r["created_at"],
                    }
                    for r in rows
                ]
            except Exception:
                return []

        if kind == "listening":
            rows = conn.execute(
                """SELECT * FROM results WHERE user_id=? AND kind='listening' AND score<? ORDER BY created_at DESC""",
                (user["id"], below),
            ).fetchall()
            return [
                {
                    "id": r["id"],
                    "kind": "listening",
                    "score": r["score"],
                    "title": f"Bài luyện Nghe #{r['id']}",
                    "subtitle": f"Điểm: {r['score']}/100",
                    "created_at": r["created_at"],
                }
                for r in rows
            ]

        if kind == "vocabulary":
            try:
                rows = conn.execute(
                    """SELECT d.id, d.word_id, d.lookup_count, d.last_looked_at, v.hanzi, v.pinyin, v.meaning, v.hsk
                       FROM dictionary_history d
                       LEFT JOIN vocabulary v ON v.id=d.word_id
                       WHERE d.user_id=? AND d.lookup_count>=2
                       ORDER BY d.last_looked_at DESC""",
                    (user["id"],),
                ).fetchall()
                return [
                    {
                        "id": r["id"],
                        "kind": "vocabulary",
                        "score": max(0.0, float(100 - r["lookup_count"] * 10)),
                        "title": r["hanzi"] or f"Từ #{r['word_id']}",
                        "subtitle": f"{r['pinyin'] or ''} · {r['meaning'] or ''} (Đã tra {r['lookup_count']} lần)",
                        "created_at": r["last_looked_at"],
                    }
                    for r in rows
                ]
            except Exception:
                return []

        rows = conn.execute(
            """SELECT r.*,p.latest_result_id,p.completed_at,p.updated_at
               FROM results r LEFT JOIN review_progress p ON p.source_result_id=r.id
               WHERE r.user_id=? AND r.kind=? AND r.score<? AND p.completed_at IS NULL
                 AND NOT EXISTS (
                   SELECT 1 FROM review_attempts retry WHERE retry.result_id=r.id
                 )
               ORDER BY r.created_at DESC""",
            (user["id"], kind, below),
        ).fetchall()
        items = []
        for row in rows:
            item = dict(row)
            latest_id = item.get("latest_result_id")
            item["latest_result"] = (dict(require_row(conn, "results", latest_id))
                                     if latest_id is not None else None)
            items.append(item)
        return items


@app.get("/api/me/review-summary")
def review_summary(below: float = Query(default=80, gt=0, le=100), user=Depends(current_user)):
    with database() as conn:
        hw_row = conn.execute(
            """SELECT COUNT(*) FROM results r
               LEFT JOIN review_progress p ON p.source_result_id=r.id
               WHERE r.user_id=? AND r.kind='handwriting' AND r.score<? AND p.completed_at IS NULL
                 AND NOT EXISTS (SELECT 1 FROM review_attempts retry WHERE retry.result_id=r.id)""",
            (user["id"], below),
        ).fetchone()
        hw_count = int(hw_row[0]) if hw_row else 0
        wt_row = conn.execute(
            """SELECT COUNT(*) FROM results r
               LEFT JOIN review_progress p ON p.source_result_id=r.id
               WHERE r.user_id=? AND r.kind='writing' AND r.score<? AND p.completed_at IS NULL
                 AND NOT EXISTS (SELECT 1 FROM review_attempts retry WHERE retry.result_id=r.id)""",
            (user["id"], below),
        ).fetchone()
        wt_count = int(wt_row[0]) if wt_row else 0
        ls_row = conn.execute(
            "SELECT COUNT(*) FROM results WHERE user_id=? AND kind='listening' AND score<?",
            (user["id"], below),
        ).fetchone()
        ls_count = int(ls_row[0]) if ls_row else 0
        rd_count = 0
        try:
            rd_row = conn.execute(
                "SELECT COUNT(*) FROM student_reading_history WHERE user_id=? AND accuracy_percent<?",
                (user["id"], below),
            ).fetchone()
            if rd_row:
                rd_count = int(rd_row[0])
        except Exception:
            pass
        ex_count = 0
        try:
            ex_row = conn.execute(
                "SELECT COUNT(*) FROM student_ai_exams WHERE user_id=? AND status='completed' AND score<?",
                (user["id"], below),
            ).fetchone()
            if ex_row:
                ex_count = int(ex_row[0])
        except Exception:
            pass
        vc_count = 0
        try:
            vc_row = conn.execute(
                "SELECT COUNT(*) FROM dictionary_history WHERE user_id=? AND lookup_count>=2",
                (user["id"],),
            ).fetchone()
            if vc_row:
                vc_count = int(vc_row[0])
        except Exception:
            pass

        total = hw_count + wt_count + ls_count + rd_count + ex_count
        return {
            "total_under_80": total,
            "reading": rd_count,
            "listening": ls_count,
            "exam": ex_count,
            "handwriting": hw_count,
            "writing": wt_count,
            "vocabulary": vc_count,
            "breakdown": {
                "reading": rd_count,
                "listening": ls_count,
                "exam": ex_count,
                "handwriting": hw_count,
                "writing": wt_count,
                "vocabulary": vc_count,
            }
        }


@app.post("/api/me/review/writing/{source_result_id}", status_code=201)
def resubmit_writing(source_result_id: int, body: WritingSubmission,
                     user=Depends(current_user)):
    with database() as conn:
        source = require_row(conn, "results", source_result_id)
        if source["user_id"] != user["id"]:
            raise HTTPException(404, "Không tìm thấy bài cần ôn tập")
        if source["kind"] != "writing" or source["score"] >= 80:
            raise HTTPException(409, "Bài này không thuộc danh sách đoạn văn cần viết lại")
    payload = json.dumps({"content": body.content, "review_of": source_result_id}, ensure_ascii=False)
    result = grade_with_ai(user["id"], "writing", payload, gemini_provider)
    now = int(time.time())
    with database() as conn:
        conn.execute(
            "INSERT INTO review_attempts(result_id,source_result_id,user_id,created_at) VALUES(?,?,?,?)",
            (result["id"], source_result_id, user["id"], now),
        )
        conn.execute(
            """INSERT INTO review_progress(source_result_id,user_id,latest_result_id,completed_at,updated_at)
               VALUES(?,?,?,?,?) ON CONFLICT(source_result_id) DO UPDATE SET
               latest_result_id=excluded.latest_result_id,
               completed_at=excluded.completed_at,updated_at=excluded.updated_at""",
            (source_result_id, user["id"], result["id"], now if result["score"] >= 80 else None, now),
        )
    result["review_completed"] = result["score"] >= 80
    result["source_result_id"] = source_result_id
    return result


@app.post("/api/me/review/handwriting/{source_result_id}", status_code=201)
def resubmit_handwriting(source_result_id: int, body: HandwritingSubmission,
                         user=Depends(current_user)):
    with database() as conn:
        source = require_row(conn, "results", source_result_id)
        if source["user_id"] != user["id"]:
            raise HTTPException(404, "Không tìm thấy chữ cần ôn tập")
        if source["kind"] != "handwriting" or source["score"] >= 80:
            raise HTTPException(409, "Chữ này không thuộc danh sách cần luyện lại")
        try:
            original_target = json.loads(source["content"])["target"]
        except (KeyError, TypeError, json.JSONDecodeError):
            raise HTTPException(409, "Bài viết tay cũ không còn đủ dữ liệu để luyện lại") from None
        if body.target != original_target:
            raise HTTPException(422, "Cần viết lại đúng chữ Hán của bài gốc")
    grade, result = grade_handwriting_submission(body, user["id"])
    now = int(time.time())
    with database() as conn:
        conn.execute(
            "INSERT INTO review_attempts(result_id,source_result_id,user_id,created_at) VALUES(?,?,?,?)",
            (result["id"], source_result_id, user["id"], now),
        )
        conn.execute(
            """INSERT INTO review_progress(source_result_id,user_id,latest_result_id,completed_at,updated_at)
               VALUES(?,?,?,?,?) ON CONFLICT(source_result_id) DO UPDATE SET
               latest_result_id=excluded.latest_result_id,
               completed_at=excluded.completed_at,updated_at=excluded.updated_at""",
            (source_result_id, user["id"], result["id"], now if result["score"] >= 80 else None, now),
        )
    return grade


@app.get("/api/me/results")
def my_results(user=Depends(current_user)):
    with database() as conn:
        rows = [dict(row) for row in conn.execute("SELECT * FROM results WHERE user_id=? ORDER BY id DESC", (user["id"],))]
        for row in rows:
            row["overrides"] = [row_to_dict(h) for h in conn.execute("SELECT old_score,new_score,reason,created_at FROM score_overrides WHERE result_id=? ORDER BY id", (row["id"],))]
        return rows


@app.get("/api/me/dashboard")
def my_dashboard(user=Depends(current_user)):
    with database() as conn:
        results = [row_to_dict(row) for row in conn.execute(
            "SELECT * FROM results WHERE user_id=? ORDER BY created_at", (user["id"],))]
        v_row = conn.execute(
            "SELECT COUNT(*) FROM dictionary_history WHERE user_id=?", (user["id"],)).fetchone()
        vocabulary_count = v_row[0] if v_row else 0

        reading_scores = []
        reading_under_80 = 0
        try:
            rd_rows = conn.execute(
                "SELECT accuracy_percent FROM student_reading_history WHERE user_id=?", (user["id"],)).fetchall()
            reading_scores = [float(r[0]) for r in rd_rows if r[0] is not None]
            reading_under_80 = sum(1 for s in reading_scores if s < 80)
        except Exception:
            pass

        exam_scores = []
        exam_under_80 = 0
        try:
            ex_rows = conn.execute(
                "SELECT score FROM student_ai_exams WHERE user_id=? AND status='completed'", (user["id"],)).fetchall()
            exam_scores = [float(r[0]) for r in ex_rows if r[0] is not None]
            exam_under_80 = sum(1 for s in exam_scores if s < 80)
        except Exception:
            pass

        vocab_weak = 0
        try:
            vw_row = conn.execute(
                "SELECT COUNT(*) FROM dictionary_history WHERE user_id=? AND lookup_count >= 2", (user["id"],)).fetchone()
            vocab_weak = vw_row[0] if vw_row else 0
        except Exception:
            pass

        nr_row = conn.execute(
            """SELECT COUNT(*) FROM results r
               LEFT JOIN review_progress p ON p.source_result_id=r.id
               WHERE r.user_id=? AND r.score<80
                 AND NOT EXISTS (
                   SELECT 1 FROM review_attempts retry WHERE retry.result_id=r.id
                 )
                 AND (r.kind='exam' OR p.completed_at IS NULL)""",
            (user["id"],),
        ).fetchone()
        classic_needs_review = nr_row[0] if nr_row else 0
        total_needs_review = classic_needs_review + reading_under_80 + exam_under_80

        activity_days = [row[0] for row in conn.execute(
            """SELECT DISTINCT date(created_at,'unixepoch','+7 hours') day FROM results WHERE user_id=?
               UNION SELECT DISTINCT date(last_looked_at,'unixepoch','+7 hours') FROM dictionary_history WHERE user_id=?
               UNION SELECT DISTINCT date(created_at,'unixepoch','+7 hours') FROM student_reading_history WHERE user_id=?
               UNION SELECT DISTINCT date(submitted_at,'unixepoch','+7 hours') FROM student_ai_exams WHERE user_id=? AND submitted_at IS NOT NULL
               UNION SELECT day FROM learner_activity_days WHERE user_id=?
               ORDER BY day DESC""",
            (user["id"], user["id"], user["id"], user["id"], user["id"]),
        )]
        attempts = {row[0] for row in conn.execute(
            "SELECT result_id FROM review_attempts WHERE user_id=?", (user["id"],))}
        latest_by_source = {row[0]: row[1] for row in conn.execute(
            "SELECT source_result_id,latest_result_id FROM review_progress WHERE user_id=?",
            (user["id"],),
        ) if row[1] is not None}
    results_by_id = {result["id"]: result for result in results}
    current_results = [
        results_by_id.get(latest_by_source.get(result["id"]), result)
        for result in results if result["id"] not in attempts
    ]
    skill_scores = {"listening": [], "reading": [], "writing": [], "handwriting": [], "exam": []}
    for result in current_results:
        skill = result["kind"]
        used_section_scores = False
        if skill == "exam":
            try:
                snapshot = json.loads(result["content"])
                sections = {q["section"] for q in snapshot["questions"]}
                if len(sections) > 1:
                    for section, section_score in snapshot.get("section_scores", {}).items():
                        if section in skill_scores:
                            skill_scores[section].append(float(section_score))
                            used_section_scores = True
                skill = next(iter(sections)) if len(sections) == 1 else "mixed"
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                skill = "mixed"
        if skill in skill_scores and not used_section_scores:
            skill_scores[skill].append(result["score"])

    # Synchronize Reading and AI Exam scores into skill_scores:
    skill_scores["reading"].extend(reading_scores)
    skill_scores["exam"].extend(exam_scores)

    from premium_benefits import protected_streak
    with database() as conn:
        conn.execute('BEGIN IMMEDIATE')
        streak = protected_streak(conn, user, activity_days)
    averages = {key: round(sum(values) / len(values), 1) if values else 0
                for key, values in skill_scores.items()}
    written_attempts = skill_scores["writing"] + skill_scores["handwriting"]
    averages["writing"] = round(sum(written_attempts) / len(written_attempts), 1) if written_attempts else 0
    all_scores = [r["score"] for r in current_results] + reading_scores + exam_scores
    overall_avg = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0

    return {
        "results": len(results) + len(reading_scores) + len(exam_scores),
        "average_score": overall_avg,
        "needs_review": total_needs_review,
        "vocabulary_count": vocabulary_count,
        "streak": streak,
        "skill_scores": averages,
        "progress_percent": overall_avg,
        "under_80_breakdown": {
            "reading": reading_under_80,
            "exam": exam_under_80,
            "listening": sum(1 for r in current_results if r["kind"] == "listening" and r["score"] < 80),
            "writing": sum(1 for r in current_results if r["kind"] == "writing" and r["score"] < 80),
            "handwriting": sum(1 for r in current_results if r["kind"] == "handwriting" and r["score"] < 80),
            "vocabulary": vocab_weak,
            "total": total_needs_review,
        },
    }


@app.get("/api/me/capability")
def my_capability(user=Depends(current_user)):
    summary = my_dashboard(user)
    if summary["results"] == 0:
        return {
            "skill_scores": summary["skill_scores"],
            "feedback": "Chưa có đủ dữ liệu. Hãy hoàn thành ít nhất một bài luyện tập.",
            "strengths": [],
            "improvements": ["Hoàn thành bài Nghe, Đọc hoặc Viết đầu tiên"],
            "updated_at": None,
            "generated_by": "default",
        }
    fingerprint = hashlib.sha256(json.dumps(summary, sort_keys=True).encode()).hexdigest()
    with database() as conn:
        cached = conn.execute("SELECT * FROM capability_reports WHERE user_id=?", (user["id"],)).fetchone()
    if cached is not None and cached["fingerprint"] == fingerprint:
        return {
            "skill_scores": summary["skill_scores"], "feedback": cached["feedback"],
            "strengths": json.loads(cached["strengths_json"]),
            "improvements": json.loads(cached["improvements_json"]),
            "updated_at": cached["updated_at"], "generated_by": "cache",
        }
    try:
        output = gemini_capability_provider(ai_settings(), json.dumps(summary, ensure_ascii=False))
        feedback = output["feedback"]
        strengths, improvements = output["strengths"], output["improvements"]
        if (not isinstance(feedback, str) or not feedback.strip()
                or not isinstance(strengths, list) or not isinstance(improvements, list)
                or any(not isinstance(value, str) or not value.strip()
                       for value in strengths + improvements)):
            raise ValueError("invalid capability report")
    except Exception as error:
        record_ai_usage(user["id"], "capability", "error")
        raise ai_http_error(error, "AI chưa thể tạo báo cáo năng lực. Vui lòng thử lại.") from None
    record_ai_usage(user["id"], "capability", "success")
    now = int(time.time())
    with database() as conn:
        conn.execute(
            """INSERT INTO capability_reports VALUES(?,?,?,?,?,?)
               ON CONFLICT(user_id) DO UPDATE SET fingerprint=excluded.fingerprint,
               feedback=excluded.feedback,strengths_json=excluded.strengths_json,
               improvements_json=excluded.improvements_json,updated_at=excluded.updated_at""",
            (user["id"], fingerprint, feedback.strip(),
             json.dumps(strengths, ensure_ascii=False),
             json.dumps(improvements, ensure_ascii=False), now),
        )
    return {"skill_scores": summary["skill_scores"], "feedback": feedback.strip(),
            "strengths": strengths, "improvements": improvements,
            "updated_at": now, "generated_by": "ai"}


def sync_review_score(conn, result_id, score):
    """An Admin correction to the latest retry also changes review completion."""
    now = int(time.time())
    conn.execute(
        "UPDATE review_progress SET completed_at=?,updated_at=? WHERE latest_result_id=?",
        (now if score >= 80 else None, now, result_id),
    )


@app.patch("/api/admin/results/{result_id}/score")
def override_score(result_id: int, body: Override, admin=Depends(admin_user)):
    with database() as conn:
        conn.execute("BEGIN IMMEDIATE")
        before = require_row(conn, "results", result_id)
        check_version(before, body.version)
        conn.execute("UPDATE results SET score=?,graded_by='admin',version=version+1 WHERE id=?", (body.score, result_id))
        sync_review_score(conn, result_id, body.score)
        conn.execute("INSERT INTO score_overrides(result_id,admin_id,old_score,new_score,reason,created_at) VALUES(?,?,?,?,?,?)",
                     (result_id, admin["id"], before["score"], body.score, body.reason, int(time.time())))
        audit(conn, admin["id"], "override", "result", result_id,
              {"score": before["score"]}, {"score": body.score, "reason": body.reason})
        return require_row(conn, "results", result_id)


@app.get("/api/admin/results/{result_id}/history")
def score_history(result_id: int, user=Depends(admin_user)):
    with database() as conn:
        require_row(conn, "results", result_id)
        return [dict(row) for row in conn.execute("SELECT s.*,u.name admin_name FROM score_overrides s JOIN users u ON u.id=s.admin_id WHERE result_id=? ORDER BY s.id DESC", (result_id,))]


@app.get("/api/admin/audit-logs")
def audit_logs(limit: int = Query(default=100, ge=1, le=500), offset: int = Query(default=0, ge=0),
               paginated: bool = False, search: str = Query('', max_length=200),
               action: str = Query('', max_length=80), entity: str = Query('', max_length=80),
               actor_id: int | None = Query(None, ge=1), from_ts: int | None = Query(None, ge=0),
               to_ts: int | None = Query(None, ge=0), user=Depends(admin_user)):
    if from_ts is not None and to_ts is not None and from_ts >= to_ts:
        raise HTTPException(422, "Ngày kết thúc phải bằng hoặc sau ngày bắt đầu")
    clauses, args = [], []
    if search.strip():
        clauses.append("(u.name LIKE ? OR u.email LIKE ? OR a.action LIKE ? OR a.entity LIKE ? OR a.entity_id LIKE ? OR a.before_json LIKE ? OR a.after_json LIKE ?)")
        args.extend(['%' + search.strip() + '%'] * 7)
    for column, value in (("a.action", action), ("a.entity", entity), ("a.actor_id", actor_id)):
        if value:
            clauses.append(column + "=?")
            args.append(value)
    if from_ts is not None:
        clauses.append("a.created_at>=?")
        args.append(from_ts)
    if to_ts is not None:
        clauses.append("a.created_at<?")
        args.append(to_ts)
    source = " FROM audit_logs a LEFT JOIN users u ON u.id=a.actor_id"
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    with database() as conn:
        rows = [row_to_dict(row) for row in conn.execute(
            "SELECT a.*,COALESCE(u.name,'Tài khoản không còn tồn tại') AS name,u.email" +
            source + where + " ORDER BY a.id DESC LIMIT ? OFFSET ?", (*args, limit, offset)).fetchall()]
        if not paginated:
            return rows
        total = conn.execute("SELECT COUNT(*)" + source + where, args).fetchone()[0]
        return {"items": rows, "total": total, "offset": offset, "limit": limit,
                "actions": [r[0] for r in conn.execute("SELECT DISTINCT action FROM audit_logs ORDER BY action").fetchall()],
                "entities": [r[0] for r in conn.execute("SELECT DISTINCT entity FROM audit_logs ORDER BY entity").fetchall()],
                "actors": [row_to_dict(r) for r in conn.execute(
                    "SELECT DISTINCT a.actor_id AS id,COALESCE(u.name,'Tài khoản không còn tồn tại') AS name" +
                    source + " ORDER BY name").fetchall()]}


@app.post("/api/me/results/{result_id}/appeals", status_code=201)
def create_appeal(result_id: int, body: Appeal, user=Depends(current_user)):
    with database() as conn:
        conn.execute("BEGIN IMMEDIATE")
        result = require_row(conn, "results", result_id)
        if result["user_id"] != user["id"]:
            raise HTTPException(404, "Không tìm thấy kết quả")
        if conn.execute("SELECT id FROM appeals WHERE result_id=? AND status='pending'", (result_id,)).fetchone():
            raise HTTPException(409, "Bài này đã có yêu cầu đang chờ xử lý")
        aid = conn.execute("INSERT INTO appeals(result_id,user_id,reason,created_at) VALUES(?,?,?,?)",
                           (result_id, user["id"], body.reason, int(time.time()))).lastrowid
        result = require_row(conn, "appeals", aid)
        audit(conn, user["id"], "create", "appeal", aid, None, result)
        return result


@app.get("/api/me/appeals")
def my_appeals(user=Depends(current_user)):
    with database() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM appeals WHERE user_id=? ORDER BY id DESC", (user["id"],))]


@app.get("/api/admin/appeals")
def admin_appeals(status: Literal["pending", "resolved"] | None = None, user=Depends(admin_user)):
    with database() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT a.*,u.name,u.email,r.kind,r.content,r.feedback,r.score,r.original_score,r.version result_version "
            "FROM appeals a JOIN users u ON u.id=a.user_id JOIN results r ON r.id=a.result_id "
            + ("WHERE a.status=? " if status else "") + "ORDER BY a.id DESC", (status,) if status else ())]


@app.patch("/api/admin/appeals/{appeal_id}")
def review_appeal(appeal_id: int, body: AppealReview, admin=Depends(admin_user)):
    with database() as conn:
        conn.execute("BEGIN IMMEDIATE")
        before = require_row(conn, "appeals", appeal_id)
        check_version(before, body.version)
        if before["status"] != "pending":
            raise HTTPException(409, "Yêu cầu đã được xử lý")
        result = require_row(conn, "results", before["result_id"])
        check_version(result, body.result_version)
        now = int(time.time())
        conn.execute("UPDATE results SET score=?,graded_by='admin',version=version+1 WHERE id=?", (body.score, result["id"]))
        sync_review_score(conn, result["id"], body.score)
        conn.execute("INSERT INTO score_overrides(result_id,admin_id,old_score,new_score,reason,created_at) VALUES(?,?,?,?,?,?)",
                     (result["id"], admin["id"], result["score"], body.score, body.response, now))
        conn.execute("UPDATE appeals SET status='resolved',response=?,reviewer_id=?,resolved_at=?,version=version+1 WHERE id=?",
                     (body.response, admin["id"], now, appeal_id))
        after = require_row(conn, "appeals", appeal_id)
        audit(conn, admin["id"], "resolve", "appeal", appeal_id, before, after)
        audit(conn, admin["id"], "override", "result", result["id"], {"score": result["score"]},
              {"score": body.score, "reason": body.response, "appeal_id": appeal_id})
        return after


@app.get("/api/me/saved-words")
def saved_words(user=Depends(current_user)):
    with database() as conn:
        return [word_json(r) for r in conn.execute(
            "SELECT v.* FROM saved_words s JOIN vocabulary v ON v.id=s.word_id WHERE s.user_id=? ORDER BY s.created_at DESC,v.id DESC",
            (user["id"],))]


@app.put("/api/me/saved-words/{word_id}", status_code=204)
def save_personal_word(word_id: int, user=Depends(current_user)):
    with database() as conn:
        require_row(conn, "vocabulary", word_id)
        conn.execute("INSERT OR IGNORE INTO saved_words(user_id,word_id,created_at) VALUES(?,?,?)",
                     (user["id"], word_id, int(time.time())))


@app.delete("/api/me/saved-words/{word_id}", status_code=204)
def remove_personal_word(word_id: int, user=Depends(current_user)):
    with database() as conn:
        conn.execute("DELETE FROM saved_words WHERE user_id=? AND word_id=?", (user["id"], word_id))


from usecase_features import register_features
register_features(app, current_user, hash_password)
from lesson_catalog import register_lessons
register_lessons(app, current_user)
from premium_benefits import register_benefits
register_benefits(app, current_user)
from ai_exam import register_ai_exam_routes
register_ai_exam_routes(app, current_user)
from ai_reading import register_reading_routes
register_reading_routes(app, current_user)


@app.get("/api/tts")
async def text_to_speech(text: str = Query(..., min_length=1, max_length=1000)):
    clean = text.strip()
    slug = hashlib.sha256(clean.encode("utf-8")).hexdigest()[:32]
    media_dir = Path(__file__).parent / "media"
    bundled_slug = '-'.join(f'{ord(c):x}' for c in clean[:24])
    bundled_file = media_dir / f"word-{bundled_slug}.mp3"
    if bundled_file.exists():
        return FileResponse(bundled_file, media_type="audio/mpeg")

    tmp_dir = Path(os.environ.get("TMPDIR", "/tmp")) / "tts_cache"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    cache_file = tmp_dir / f"tts-{slug}.mp3"
    if cache_file.exists():
        return FileResponse(cache_file, media_type="audio/mpeg")

    # Try edge-tts if installed
    try:
        import edge_tts
        communicate = edge_tts.Communicate(clean, "zh-CN-XiaoxiaoNeural", rate="-10%")
        await communicate.save(str(cache_file))
        return FileResponse(cache_file, media_type="audio/mpeg")
    except Exception:
        pass

    # Fallback to Google Translate TTS with sentence chunking
    try:
        import urllib.parse
        import re
        import httpx
        chunks = []
        current = ""
        sentences = re.split(r'([。！？；;\n]+)', clean)
        for part in sentences:
            if not part:
                continue
            if len(current) + len(part) <= 140:
                current += part
            else:
                if current:
                    chunks.append(current)
                current = part
                while len(current) > 140:
                    chunks.append(current[:140])
                    current = current[140:]
        if current:
            chunks.append(current)

        audio_chunks = []
        async with httpx.AsyncClient() as client:
            for chunk in chunks:
                encoded = urllib.parse.quote(chunk)
                url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl=zh-CN&client=tw-ob&q={encoded}"
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10.0)
                if resp.status_code == 200:
                    audio_chunks.append(resp.content)
                else:
                    raise Exception(f"Google TTS returned status {resp.status_code}")
        if audio_chunks:
            cache_file.write_bytes(b"".join(audio_chunks))
            return FileResponse(cache_file, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(500, f"Lỗi tạo phát âm: {e}")
    raise HTTPException(500, "Không thể tạo phát âm")


ADMIN_DIR = Path(__file__).resolve().parent.parent / "admin"
from sepay_gateway import register_gateway
register_gateway(app)

WEB_DIR = Path(os.environ["WEB_APP_DIR"]).resolve() if os.getenv("WEB_APP_DIR") else None
app.mount("/admin/assets", StaticFiles(directory=ADMIN_DIR), name="admin-assets")
app.mount("/media", StaticFiles(directory=Path(__file__).parent / "media", check_dir=False), name="media")


@app.get("/admin", include_in_schema=False)
@app.get("/admin/", include_in_schema=False)
def admin_page():
    # The shell shows login only. Every administrative data route requires admin_user.
    return FileResponse(ADMIN_DIR / "index.html")


@app.get("/appearance", include_in_schema=False)
def appearance_page():
    return FileResponse(ADMIN_DIR / "appearance.html")


@app.get("/review", include_in_schema=False)
def learner_review_page():
    return FileResponse(ADMIN_DIR / "review.html")


@app.get("/exam", include_in_schema=False)
@app.get("/exam/", include_in_schema=False)
def learner_exam_page():
    return FileResponse(ADMIN_DIR / "exam.html")


@app.get("/reading", include_in_schema=False)
@app.get("/reading/", include_in_schema=False)
def learner_reading_page():
    return FileResponse(ADMIN_DIR / "reading.html")


@app.middleware("http")
async def fresh_web_assets(request, call_next):
    response = await call_next(request)
    if not request.url.path.startswith(("/api/", "/media/")):
        response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


# ==========================================
# HanziGo Premium & SePay Payment Integration
# ==========================================

@app.get("/api/premium/plans")
def get_premium_plans():
    """Return available HanziGo Premium subscription plans, comparison table, and payment info."""
    with database() as conn:
        cfg = get_sepay_config(conn)
    return {
        "plans": PLAN_PRICES,
        "comparison": COMPARISON_FEATURES,
        "payment_info": {
            "bank_name": cfg["bank_name"],
            "bank_account": cfg["bank_account"],
            "account_holder": cfg["account_holder"],
            "is_active": bool(cfg["is_active"]),
        }
    }


@app.get("/api/premium/me")
def get_my_premium_status(user=Depends(current_user)):
    """Return current user's HanziGo Premium membership details."""
    from sepay_gateway import reconcile_recent_orders
    reconcile_recent_orders(user['id'])
    now = int(time.time())
    with database() as conn:
        u = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
        from premium_benefits import benefits
        benefit_state = benefits(conn, dict(u))
        orders = conn.execute(
            """SELECT id, order_code, plan_type, amount, status, created_at, completed_at
               FROM premium_orders WHERE user_id = ? ORDER BY id DESC LIMIT 5""",
            (user["id"],)
        ).fetchall()

    p_until = u["premium_until"] if u else 0
    is_premium = bool(p_until > now)
    days_left = max(0, (p_until - now) // 86400) if is_premium else 0

    return {
        "is_premium": is_premium,
        "premium_until": p_until,
        "days_remaining": days_left,
        "streak_freezes": benefit_state['streak_freezes'],
        "recent_orders": [row_to_dict(o) for o in orders]
    }


@app.post("/api/premium/orders", status_code=201)
def create_order(body: CreatePremiumOrderRequest, user=Depends(current_user)):
    """Create a subscription order for 1 month or 1 year with optional voucher."""
    with database() as conn:
        conn.execute("BEGIN IMMEDIATE")
        order = create_premium_order(conn, user["id"], body.plan_type, body.voucher_code)
    return order


@app.get("/api/premium/orders/{order_code}/status")
def check_order_status(order_code: str, user=Depends(current_user)):
    """Verify payment first, then expire unpaid checkout after ten minutes."""
    from sepay_gateway import reconcile_order
    reconcile_order(order_code.strip(), user['id'])
    now = int(time.time())
    with database() as conn:
        row = conn.execute(
            "SELECT * FROM premium_orders WHERE order_code = ? AND user_id = ?",
            (order_code.strip(), user["id"])
        ).fetchone()
        if not row:
            raise HTTPException(404, "Không tìm thấy đơn hàng hoặc đơn đã hết thời gian thanh toán.")
        
        order = row_to_dict(row)
        # Preserve the order for authenticated late payment confirmation.
        if order["status"] == "pending" and (now - order["created_at"]) >= 600:
            conn.execute("UPDATE premium_orders SET status='cancelled' WHERE id = ? AND status='pending'", (order["id"],))
            return {
                "order_code": order["order_code"],
                "status": "expired",
                "is_completed": False,
                "is_expired": True,
                "message": "Đã hết thời gian chờ 10 phút. Lịch sử đơn được giữ để đối chiếu nếu đã chuyển tiền."
            }

        u = conn.execute("SELECT premium_until FROM users WHERE id = ?", (user["id"],)).fetchone()

    is_completed = order["status"] == "completed"
    seconds_left = max(0, 600 - (now - order["created_at"])) if order["status"] == "pending" else 0

    return {
        "order_code": order["order_code"],
        "status": order["status"],
        "is_completed": is_completed,
        "is_expired": order["status"] == "cancelled",
        "seconds_remaining": seconds_left,
        "amount": order["amount"],
        "plan_type": order["plan_type"],
        "premium_until": u["premium_until"] if u else 0,
        "is_premium": bool(u and u["premium_until"] > now)
    }


@app.post("/api/premium/redeem-voucher")
def redeem_voucher(body: RedeemVoucherRequest, user=Depends(current_user)):
    """Redeem voucher: immediately activate 1-month free Premium or report percentage discount."""
    with database() as conn:
        result = redeem_voucher_direct(conn, user["id"], body.code)
    return result


@app.post("/api/payment/sepay-webhook")
async def sepay_webhook(request: Request):
    """Receive SePay bank transfer webhook and automatically activate HanziGo Premium."""
    try:
        raw_body = await request.body()
        payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
    except Exception:
        raise HTTPException(400, "Invalid JSON payload.")

    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    signature_header = request.headers.get("x-sepay-signature") or request.headers.get("X-SePay-Signature")
    timestamp_header = request.headers.get("x-sepay-timestamp") or request.headers.get("X-SePay-Timestamp")
    custom_secret = (
        request.headers.get("x-secret-key") or request.headers.get("X-Secret-Key") or
        request.headers.get("x-api-key") or request.headers.get("X-Api-Key")
    )
    merchant_header = request.headers.get("x-merchant-id") or request.headers.get("X-Merchant-Id")

    with database() as conn:
        conn.execute("BEGIN IMMEDIATE")
        if isinstance(payload, dict) and 'notification_type' in payload:
            from sepay_gateway import process_ipn
            return process_ipn(conn, payload, request.headers.get('x-secret-key'))
        result = process_sepay_webhook(
            conn,
            payload,
            auth_header=auth_header,
            signature_header=signature_header,
            timestamp_header=timestamp_header,
            custom_secret=custom_secret,
            merchant_header=merchant_header,
            raw_body=raw_body
        )
    return result


# ==========================================
# Admin Management: HanziGo Premium & SePay
# ==========================================

@app.get("/api/admin/premium/dashboard")
def admin_premium_dashboard(user=Depends(admin_user)):
    """Return overview metrics for HanziGo Premium, SePay transactions, and Vouchers."""
    now = int(time.time())
    with database() as conn:
        # Mark ten-minute expired orders; never delete payment history.
        cleanup_expired_pending_orders(conn)
        active_subscribers = conn.execute("SELECT COUNT(*) FROM users WHERE premium_until > ?", (now,)).fetchone()[0]
        total_orders = conn.execute("SELECT COUNT(*) FROM premium_orders").fetchone()[0]
        completed_orders = conn.execute("SELECT COUNT(*) FROM premium_orders WHERE status = 'completed'").fetchone()[0]
        pending_orders = conn.execute("SELECT COUNT(*) FROM premium_orders WHERE status = 'pending'").fetchone()[0]
        total_revenue = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM premium_orders WHERE status = 'completed'").fetchone()[0]
        total_vouchers = conn.execute("SELECT COUNT(*) FROM vouchers").fetchone()[0]
        ai_vouchers = conn.execute("SELECT COUNT(*) FROM vouchers WHERE created_by = 'ai'").fetchone()[0]
        admin_vouchers = conn.execute("SELECT COUNT(*) FROM vouchers WHERE created_by != 'ai'").fetchone()[0]

    return {
        "active_subscribers": active_subscribers,
        "total_orders": total_orders,
        "completed_orders": completed_orders,
        "pending_orders": pending_orders,
        "total_revenue": total_revenue,
        "total_vouchers": total_vouchers,
        "ai_vouchers": ai_vouchers,
        "admin_vouchers": admin_vouchers
    }


@app.get("/api/admin/premium/transactions")
def admin_premium_transactions(
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user=Depends(admin_user)
):
    """List orders; mark unpaid orders expired after ten minutes, retaining history."""
    with database() as conn:
        # Mark ten-minute expired orders; never delete payment history.
        cleanup_expired_pending_orders(conn)
        query = """
            SELECT o.*, u.name AS user_name, u.email AS user_email
            FROM premium_orders o
            LEFT JOIN users u ON u.id = o.user_id
        """
        params: list[Any] = []
        if status:
            query += " WHERE o.status = ?"
            params.append(status)
        query += " ORDER BY o.id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = conn.execute(query, params).fetchall()
        total_count = conn.execute(
            "SELECT COUNT(*) FROM premium_orders" + (" WHERE status = ?" if status else ""),
            ([status] if status else [])
        ).fetchone()[0]

    return {
        "total": total_count,
        "items": [row_to_dict(r) for r in rows]
    }



@app.post("/api/admin/premium/transactions/{order_id}/activate")
def admin_activate_order(order_id: int, user=Depends(admin_user)):
    """Admin manual activation is disabled. Transactions must reflect real money received via SePay."""
    raise HTTPException(
        403,
        "Không thể thao tác thủ công trên giao dịch SePay. Trạng thái chỉ được cập nhật tự động khi SePay nhận đúng tiền thật từ ngân hàng."
    )



@app.get("/api/admin/premium/sepay-config")
def admin_get_sepay_config(user=Depends(admin_user)):
    """Retrieve SePay configuration and webhook guide."""
    with database() as conn:
        cfg = get_sepay_config(conn)
    cfg["api_key_configured"] = bool(cfg.pop("api_key", ""))
    cfg["gateway_configured"] = bool(os.getenv("SEPAY_SECRET_KEY") and os.getenv("SEPAY_MERCHANT_ID"))
    return {
        "config": cfg,
        "webhook_url": "/api/payment/sepay-webhook",
        "ipn_url": "/api/payment/sepay-ipn",
        "instructions": [
            "1. Đăng nhập vào tài khoản SePay của bạn tại https://my.sepay.vn",
            "2. Vào mục 'Kết nối ngân hàng', thêm tài khoản ngân hàng của bạn (Số tài khoản, Tên ngân hàng, Tên chủ tài khoản).",
            "3. Cập nhật thông tin ngân hàng tương ứng vào biểu mẫu bên dưới.",
            "4. Vào mục 'Tích hợp Webhook' trên SePay, tạo webhook mới:",
            "   - URL nhận webhook: https://<domain-cua-ban>/api/payment/sepay-webhook",
            "   - Kiểu dữ liệu: JSON",
            "   - Trạng thái: Kích hoạt",
            "5. Webhook ngân hàng bắt buộc xác thực API Key. Merchant Secret Key thuộc cổng thanh toán, đặt riêng trong SEPAY_SECRET_KEY trên backend.",
            "6. Hệ thống tự động nhận diện mã đơn hàng HZGxxxxxx trong nội dung chuyển khoản và kích hoạt hội viên VIP tức thì!"
        ]
    }


@app.put("/api/admin/premium/sepay-config")
def admin_update_sepay_config(body: SepayConfigUpdate, user=Depends(admin_user)):
    """Update SePay payment configuration."""
    with database() as conn:
        updated = update_sepay_config(
            conn,
            bank_name=body.bank_name,
            bank_account=body.bank_account,
            account_holder=body.account_holder,
            api_key=body.api_key,
            merchant_id=body.merchant_id,
            is_active=body.is_active
        )
    updated["api_key_configured"] = bool(updated.pop("api_key", ""))
    return {"success": True, "config": updated}


@app.get("/api/admin/premium/vouchers")
def admin_list_vouchers(
    created_by: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    user=Depends(admin_user)
):
    """List all discount and free-month vouchers, distinguishing Admin vs AI generated."""
    with database() as conn:
        query = """
            SELECT v.*, u.email AS assigned_user_email
            FROM vouchers v
            LEFT JOIN users u ON u.id = v.user_id
        """
        params: list[Any] = []
        if created_by:
            query += " WHERE v.created_by = ?"
            params.append(created_by)
        query += " ORDER BY v.id DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(query, params).fetchall()

    return {"items": [row_to_dict(r) for r in rows]}


@app.post("/api/admin/premium/vouchers", status_code=201)
def admin_create_voucher(body: AdminCreateVoucherRequest, user=Depends(admin_user)):
    """Create a new discount or 1-month free voucher."""
    code = body.code.strip().upper() if body.code else f"VIP{secrets.randbelow(90000) + 10000}"
    now = int(time.time())

    with database() as conn:
        exists = conn.execute("SELECT 1 FROM vouchers WHERE UPPER(code) = ?", (code,)).fetchone()
        if exists:
            raise HTTPException(400, f"Mã voucher '{code}' đã tồn tại.")

        vid = conn.execute(
            """INSERT INTO vouchers (
                code, discount_percent, is_free_month, max_uses, used_count,
                created_by, description, is_active, expires_at, created_at
            ) VALUES (?, ?, ?, ?, 0, 'admin', ?, 1, ?, ?)""",
            (
                code,
                body.discount_percent if not body.is_free_month else 100,
                1 if body.is_free_month else 0,
                body.max_uses,
                body.description or ("1 Tháng HanziGo Premium miễn phí" if body.is_free_month else f"Giảm {body.discount_percent}% gói HanziGo Premium"),
                body.expires_at,
                now
            )
        ).lastrowid
        created = conn.execute("SELECT * FROM vouchers WHERE id = ?", (vid,)).fetchone()

    return row_to_dict(created)


@app.delete("/api/admin/premium/vouchers/{voucher_id}")
def admin_delete_voucher(voucher_id: int, user=Depends(admin_user)):
    """Delete or deactivate a voucher."""
    with database() as conn:
        res = conn.execute("DELETE FROM vouchers WHERE id = ?", (voucher_id,))
        if res.rowcount == 0:
            raise HTTPException(404, "Không tìm thấy mã voucher.")
    return {"success": True, "message": "Đã xóa mã voucher thành công."}


@app.get("/flutter_service_worker.js", include_in_schema=False)
def retire_flutter_worker():
    # Replace legacy cache-first workers, including on already installed clients.
    return HTMLResponse("""
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', event => event.waitUntil((async () => {
  for (const key of await caches.keys()) {
    if (['flutter-app-cache', 'flutter-temp-cache', 'flutter-app-manifest'].includes(key)) await caches.delete(key);
  }
  await self.registration.unregister();
  for (const client of await self.clients.matchAll({type: 'window'})) client.navigate(client.url);
})()));
""", media_type="application/javascript")


@app.get("/update-app", include_in_schema=False)
def update_app():
    return HTMLResponse("""<!doctype html><html lang="vi"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cập nhật HanziGo</title><body style="font:18px sans-serif;padding:32px;background:#f5f7f4">
<p id="status">Đang cập nhật giao diện HanziGo…</p>
<script>
(async () => {
  try {
    if ('serviceWorker' in navigator) {
      for (const r of await navigator.serviceWorker.getRegistrations()) {
        const worker = r.active || r.waiting || r.installing;
        if (worker && new URL(worker.scriptURL).pathname === '/flutter_service_worker.js') await r.unregister();
      }
    }
    if ('caches' in window) {
      for (const key of await caches.keys()) {
        if (['flutter-app-cache', 'flutter-temp-cache', 'flutter-app-manifest'].includes(key)) await caches.delete(key);
      }
    }
    location.replace('/?updated=' + Date.now());
  } catch (error) {
    document.getElementById('status').textContent = 'Chưa cập nhật được. Hãy tải lại trang để thử lại.';
  }
})();
</script></body></html>""")


web_root = WEB_DIR
if web_root is not None:
    WEB_VERSION = hashlib.sha256((web_root / "main.dart.js").read_bytes()).hexdigest()[:16]

    @app.get("/", include_in_schema=False)
    @app.get("/index.html", include_in_schema=False)
    def versioned_web_index():
        assert web_root is not None
        html = (web_root / "index.html").read_text(encoding="utf-8")
        return HTMLResponse(html.replace('src="flutter_bootstrap.js"',
            f'src="/_app/{WEB_VERSION}/flutter_bootstrap.js"'))

    @app.get("/_app/{version}/flutter_bootstrap.js", include_in_schema=False)
    def versioned_bootstrap(version: str):
        if version != WEB_VERSION:
            raise HTTPException(404, "Build no longer available")
        assert web_root is not None
        script = (web_root / "flutter_bootstrap.js").read_text(encoding="utf-8")
        script = script.replace('"mainJsPath":"main.dart.js"',
            f'"mainJsPath":"/_app/{WEB_VERSION}/main.dart.js"')
        return HTMLResponse(script, media_type="application/javascript")

    @app.get("/_app/{version}/main.dart.js", include_in_schema=False)
    def versioned_main_js(version: str):
        if version != WEB_VERSION:
            raise HTTPException(404, "Build no longer available")
        assert web_root is not None
        return FileResponse(web_root / "main.dart.js", media_type="application/javascript")

    app.mount("/", StaticFiles(directory=web_root, html=True), name="learner-web")
