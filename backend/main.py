"""HanziGo Admin API. Run: python -m uvicorn main:app --port 8010."""
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from database import audit, database, init_db
from models import AIConfig, Exam, ExamUpdate, Login, Override, Register, Submission, UserUpdate, Word, WordUpdate


@asynccontextmanager
async def lifespan(app):
    init_db()
    yield


app = FastAPI(title="HanziGo · Chinese Learning API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware,
                   allow_origins=os.getenv("FRONTEND_ORIGINS", "http://localhost:5173,http://localhost:8080").split(","),
                   allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
                   allow_headers=["Authorization", "Content-Type"])


def hash_password(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 600_000).hex()


def public_user(row):
    return {key: row[key] for key in ("id", "name", "email", "role", "is_active", "created_at")}


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
    return dict(row)


def admin_user(user=Depends(current_user)):
    if user["role"] != "admin":
        raise HTTPException(403, "Chỉ quản trị viên được truy cập")
    return user


def require_row(conn, table, row_id):
    # table is always an internal constant, never request input.
    row = conn.execute(f"SELECT * FROM {table} WHERE id=?", (row_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "Không tìm thấy dữ liệu")
    return dict(row)


def check_version(row, version):
    if row["version"] != version:
        raise HTTPException(409, "Dữ liệu đã được người khác cập nhật. Hãy tải lại trước khi lưu.")


@app.get("/api/health")
def health():
    with database() as conn:
        conn.execute("SELECT 1").fetchone()
    return {"status": "ok", "product": "HanziGo"}


@app.post("/api/auth/register", status_code=201)
def register(body: Register):
    salt = secrets.token_hex(16)
    password_hash = hash_password(body.password, salt)
    try:
        with database() as conn:
            uid = conn.execute("INSERT INTO users(name,email,password_hash,salt,created_at) VALUES(?,?,?,?,?)",
                               (body.name, body.email, password_hash, salt, int(time.time()))).lastrowid
            return session(conn, require_row(conn, "users", uid))
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Email đã được sử dụng")


@app.post("/api/auth/login")
def login(body: Login):
    with database() as conn:
        row = conn.execute("SELECT * FROM users WHERE email=?", (body.email.lower(),)).fetchone()
        # Perform the same expensive hash even when the email does not exist.
        candidate = hash_password(body.password, row["salt"] if row else "00" * 16)
        if row is None or not hmac.compare_digest(candidate, row["password_hash"]):
            raise HTTPException(401, "Email hoặc mật khẩu không đúng")
        if not row["is_active"]:
            raise HTTPException(403, "Tài khoản đã bị khóa")
        return session(conn, row)


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
        totals = dict(conn.execute("SELECT COUNT(*) users, COALESCE(SUM(is_active),0) active_users, COALESCE(SUM(role='admin'),0) admins FROM users").fetchone())
        for table in ("vocabulary", "exams", "results"):
            totals[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        totals["average_score"] = conn.execute("SELECT COALESCE(ROUND(AVG(score),1),0) FROM results").fetchone()[0]
        totals["ai_success"] = conn.execute("SELECT COUNT(*) FROM ai_usage WHERE status='success'").fetchone()[0]
        totals["ai_errors"] = conn.execute("SELECT COUNT(*) FROM ai_usage WHERE status='error'").fetchone()[0]
        activity = [dict(row) for row in conn.execute("SELECT a.id,u.name,a.action,a.entity,a.entity_id,a.created_at FROM audit_logs a JOIN users u ON u.id=a.actor_id ORDER BY a.id DESC LIMIT 10")]
    return {"totals": totals, "recent_activity": activity}


@app.get("/api/admin/users")
def users(search: str = Query(default="", max_length=120), role: Literal["student", "admin"] | None = None,
          active: bool | None = None, user=Depends(admin_user)):
    query = "SELECT * FROM users WHERE (name LIKE ? OR email LIKE ?)"
    values = [f"%{search}%", f"%{search}%"]
    if role:
        query += " AND role=?"
        values.append(role)
    if active is not None:
        query += " AND is_active=?"
        values.append(int(active))
    with database() as conn:
        return [public_user(row) for row in conn.execute(query + " ORDER BY id DESC", values)]


@app.patch("/api/admin/users/{user_id}")
def update_user(user_id: int, body: UserUpdate, admin=Depends(admin_user)):
    if user_id == admin["id"] and (not body.is_active or body.role != "admin"):
        raise HTTPException(400, "Không thể tự khóa hoặc hạ quyền tài khoản đang dùng")
    with database() as conn:
        conn.execute("BEGIN IMMEDIATE")
        before = require_row(conn, "users", user_id)
        if before["role"] == "admin" and before["is_active"] and (not body.is_active or body.role != "admin"):
            if conn.execute("SELECT COUNT(*) FROM users WHERE role='admin' AND is_active=1").fetchone()[0] <= 1:
                raise HTTPException(409, "Phải giữ ít nhất một quản trị viên hoạt động")
        conn.execute("UPDATE users SET role=?,is_active=? WHERE id=?", (body.role, int(body.is_active), user_id))
        if not body.is_active or body.role != before["role"]:
            conn.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
        after = public_user(require_row(conn, "users", user_id))
        audit(conn, admin["id"], "update", "user", user_id, public_user(before), after)
    return after


def word_json(row):
    item = dict(row)
    item["strokes"] = json.loads(item.pop("strokes_json"))
    return item


@app.get("/api/vocabulary")
def vocabulary(search: str = Query(default="", max_length=120), hsk: int | None = Query(default=None, ge=1, le=6)):
    query = "SELECT * FROM vocabulary WHERE (hanzi LIKE ? OR pinyin LIKE ? OR meaning LIKE ?)"
    values = [f"%{search}%"] * 3
    if hsk:
        query += " AND hsk=?"
        values.append(hsk)
    with database() as conn:
        return [word_json(row) for row in conn.execute(query + " ORDER BY hsk,id", values)]


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
        raise HTTPException(409, "Từ đang được dùng trong đề thi. Hãy gỡ liên kết trước khi xóa.")


def exam_json(row, learner=False):
    item = dict(row)
    item["questions"] = json.loads(item.pop("questions_json"))
    if learner:
        for q in item["questions"]:
            for key in ("answer", "explanation", "transcript"):
                q.pop(key, None)
    return item


@app.get("/api/admin/exams")
def admin_exams(hsk: int | None = Query(default=None, ge=1, le=6), user=Depends(admin_user)):
    with database() as conn:
        rows = conn.execute("SELECT * FROM exams" + (" WHERE hsk=?" if hsk else "") + " ORDER BY id DESC", (hsk,) if hsk else ())
        return [exam_json(row) for row in rows]


@app.get("/api/exams")
def learner_exams(hsk: int | None = Query(default=None, ge=1, le=6), user=Depends(current_user)):
    with database() as conn:
        rows = conn.execute("SELECT * FROM exams WHERE status='published'" + (" AND hsk=?" if hsk else "") + " ORDER BY hsk,id", (hsk,) if hsk else ())
        return [exam_json(row, learner=True) for row in rows]


def save_exam(body, admin, exam_id=None):
    questions = [q.model_dump() for q in body.questions]
    with database() as conn:
        conn.execute("BEGIN IMMEDIATE")
        for q in questions:
            if q["word_id"] is not None:
                require_row(conn, "vocabulary", q["word_id"])
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


@app.post("/api/exams/{exam_id}/submit", status_code=201)
def submit(exam_id: int, body: Submission, user=Depends(current_user)):
    with database() as conn:
        conn.execute("BEGIN IMMEDIATE")
        exam = require_row(conn, "exams", exam_id)
        if exam["status"] != "published":
            raise HTTPException(404, "Đề thi chưa được phát hành")
        check_version(exam, body.version)
        questions = json.loads(exam["questions_json"])
        if any(q["section"] == "writing" and not q["options"] for q in questions):
            raise HTTPException(422, "Bài viết tự do cần module chấm Writing; không tự động chấm bằng so khớp văn bản.")
        if set(body.answers) != {q["id"] for q in questions}:
            raise HTTPException(422, "Cần nộp đúng danh sách mã câu hỏi của đề")
        score = round(100 * sum(body.answers[q["id"]].strip() == q["answer"] for q in questions) / len(questions), 2)
        snapshot = json.dumps({"exam_title": exam["title"], "exam_version": exam["version"], "questions": questions, "answers": body.answers}, ensure_ascii=False)
        rid = conn.execute("INSERT INTO results(user_id,exam_id,kind,content,score,original_score,graded_by,created_at) VALUES(?,?,'exam',?,?,?,'automatic',?)",
                           (user["id"], exam_id, snapshot, score, score, int(time.time()))).lastrowid
        return require_row(conn, "results", rid)


@app.get("/api/admin/ai-config")
def get_ai_config(user=Depends(admin_user)):
    with database() as conn:
        result = require_row(conn, "ai_config", 1)
    result["key_configured"] = bool(os.getenv("AI_API_KEY", "").strip())
    result["ready"] = bool(result["enabled"] and result["key_configured"] and result["model"] != "configure-your-model")
    return result


@app.put("/api/admin/ai-config")
def update_ai_config(body: AIConfig, admin=Depends(admin_user)):
    if body.enabled and (not os.getenv("AI_API_KEY", "").strip() or body.model == "configure-your-model"):
        raise HTTPException(422, "Cần đặt AI_API_KEY trên máy chủ và chọn model trước khi bật AI")
    with database() as conn:
        conn.execute("BEGIN IMMEDIATE")
        before = require_row(conn, "ai_config", 1)
        check_version(before, body.version)
        conn.execute("UPDATE ai_config SET model=?,system_prompt=?,temperature=?,max_tokens=?,enabled=?,version=version+1 WHERE id=1",
                     (body.model, body.system_prompt, body.temperature, body.max_tokens, int(body.enabled)))
        audit(conn, admin["id"], "update", "ai_config", 1, before, require_row(conn, "ai_config", 1))
    return get_ai_config(admin)


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


@app.get("/api/me/results")
def my_results(user=Depends(current_user)):
    with database() as conn:
        rows = [dict(row) for row in conn.execute("SELECT * FROM results WHERE user_id=? ORDER BY id DESC", (user["id"],))]
        for row in rows:
            row["overrides"] = [dict(h) for h in conn.execute("SELECT old_score,new_score,reason,created_at FROM score_overrides WHERE result_id=? ORDER BY id", (row["id"],))]
        return rows


@app.get("/api/me/dashboard")
def my_dashboard(user=Depends(current_user)):
    with database() as conn:
        return dict(conn.execute("SELECT COUNT(*) results,COALESCE(ROUND(AVG(score),1),0) average_score,COALESCE(SUM(score<80),0) needs_review FROM results WHERE user_id=?", (user["id"],)).fetchone())


@app.patch("/api/admin/results/{result_id}/score")
def override_score(result_id: int, body: Override, admin=Depends(admin_user)):
    with database() as conn:
        conn.execute("BEGIN IMMEDIATE")
        before = require_row(conn, "results", result_id)
        check_version(before, body.version)
        conn.execute("UPDATE results SET score=?,graded_by='admin',version=version+1 WHERE id=?", (body.score, result_id))
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
def audit_logs(limit: int = Query(default=100, ge=1, le=500), offset: int = Query(default=0, ge=0), user=Depends(admin_user)):
    with database() as conn:
        return [dict(row) for row in conn.execute("SELECT a.*,u.name FROM audit_logs a JOIN users u ON u.id=a.actor_id ORDER BY a.id DESC LIMIT ? OFFSET ?", (limit, offset))]


ADMIN_DIR = Path(__file__).resolve().parent.parent / "admin"
app.mount("/admin/assets", StaticFiles(directory=ADMIN_DIR), name="admin-assets")


@app.get("/admin", include_in_schema=False)
@app.get("/admin/", include_in_schema=False)
def admin_page():
    # The shell shows login only. Every administrative data route requires admin_user.
    return FileResponse(ADMIN_DIR / "index.html")
