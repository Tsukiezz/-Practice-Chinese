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
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from database import audit, database, init_db
from models import Appeal, AppealReview
from models import (AIConfig, DictionaryLookup, Exam, ExamUpdate,
                    HandwritingSubmission, Login, Override, Register,
                    Submission, UserUpdate, Word, WordUpdate, WritingSubmission)
from services import (configured_api_key, configured_model, evaluate_with_ai,
                      gemini_capability_provider, gemini_exam_provider,
                      gemini_handwriting_provider, gemini_provider, grade_with_ai, ai_settings,
                      record_ai_usage)


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
    return {key: row[key] for key in ("id", "name", "email", "role", "is_active", "created_at", "version")}


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
        check_version(before, body.version)
        if before["role"] == "admin" and before["is_active"] and (not body.is_active or body.role != "admin"):
            if conn.execute("SELECT COUNT(*) FROM users WHERE role='admin' AND is_active=1").fetchone()[0] <= 1:
                raise HTTPException(409, "Phải giữ ít nhất một quản trị viên hoạt động")
        conn.execute("UPDATE users SET role=?,is_active=?,version=version+1 WHERE id=?", (body.role, int(body.is_active), user_id))
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
    item = dict(row)
    item["strokes"] = json.loads(item.pop("strokes_json"))
    return item


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
def submit(exam_id: int, body: Submission, user=Depends(current_user), grader=Depends(get_exam_ai_grader)):
    with database() as conn:
        exam = require_row(conn, "exams", exam_id)
        if exam["status"] != "published":
            raise HTTPException(404, "Đề thi chưa được phát hành")
        check_version(exam, body.version)
        questions = json.loads(exam["questions_json"])
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
        grade = grade_function(user["id"], grading_content)
        score, feedback, graded_by = grade["score"], grade["feedback"], "ai"
        ai_review_items = grade.get("review_items", [])
        section_scores = grade.get("section_scores", {section: score for section in sections})
    else:
        score = round(100 * sum(body.answers[q["id"]].strip() == q["answer"] for q in questions) / len(questions), 2)
        feedback, graded_by = "", "automatic"
        ai_review_items = []
        section_scores = {}

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
        return require_row(conn, "results", rid)


@app.get("/api/admin/ai-config")
def get_ai_config(user=Depends(admin_user)):
    with database() as conn:
        result = require_row(conn, "ai_config", 1)
    result["model"] = configured_model(result)
    result["key_configured"] = bool(configured_api_key())
    result["ready"] = bool(result["enabled"] and result["key_configured"] and result["model"])
    return result


@app.put("/api/admin/ai-config")
def update_ai_config(body: AIConfig, admin=Depends(admin_user)):
    if body.enabled and (not configured_api_key() or body.model == "configure-your-model"):
        raise HTTPException(422, "Cần đặt GEMINI_API_KEY trên máy chủ và chọn model trước khi bật AI")
    with database() as conn:
        conn.execute("BEGIN IMMEDIATE")
        before = require_row(conn, "ai_config", 1)
        check_version(before, body.version)
        conn.execute("UPDATE ai_config SET model=?,system_prompt=?,temperature=?,max_tokens=?,enabled=?,version=version+1 WHERE id=1",
                     (body.model, body.system_prompt, body.temperature, body.max_tokens, int(body.enabled)))
        audit(conn, admin["id"], "update", "ai_config", 1, before, require_row(conn, "ai_config", 1))
    return get_ai_config(admin)


@app.post("/api/admin/ai-config/test")
def test_ai_connection(admin=Depends(admin_user)):
    from services import ai_settings, record_ai_usage
    from ai_provider import gemini_grade
    settings = ai_settings()
    try:
        gemini_grade(settings, "Bài kiểm tra kết nối: 你好。")
    except Exception:
        record_ai_usage(admin["id"], "connection_test", "error")
        raise HTTPException(502, "Không nhận được phản hồi AI hợp lệ. Kiểm tra model, khóa và hạn mức trên máy chủ.") from None
    record_ai_usage(admin["id"], "connection_test", "success")
    return {"status": "ok", "message": "Đã nhận phản hồi hợp lệ từ Gemini. Không tạo điểm học viên."}


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


def grade_handwriting_submission(body: HandwritingSubmission, user_id: int):
    with database() as conn:
        word = conn.execute("SELECT * FROM vocabulary WHERE hanzi=?", (body.target,)).fetchone()
    if word is None:
        raise HTTPException(404, "Chữ Hán chưa có trong kho nét chuẩn")
    standard = json.loads(word["strokes_json"])
    if not standard:
        raise HTTPException(422, "Chữ Hán chưa có dữ liệu nét chuẩn")
    payload = json.dumps({
        "target": body.target,
        "standard_strokes": standard,
        "submitted_strokes": [[point.model_dump() for point in stroke] for stroke in body.strokes],
    }, ensure_ascii=False)
    return grade_with_ai(user_id, "handwriting", payload, gemini_handwriting_provider)


@app.post("/api/handwriting/submit", status_code=201)
def submit_handwriting(body: HandwritingSubmission, user=Depends(current_user)):
    return grade_handwriting_submission(body, user["id"])


@app.get("/api/me/review-items")
def review_items(kind: Literal["handwriting", "writing"],
                 below: float = Query(default=80, gt=0, le=100),
                 user=Depends(current_user)):
    with database() as conn:
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
    result = grade_handwriting_submission(body, user["id"])
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
        results = [dict(row) for row in conn.execute(
            "SELECT * FROM results WHERE user_id=? ORDER BY created_at", (user["id"],))]
        vocabulary_count = conn.execute(
            "SELECT COUNT(*) FROM dictionary_history WHERE user_id=?", (user["id"],)).fetchone()[0]
        needs_review = conn.execute(
            """SELECT COUNT(*) FROM results r
               LEFT JOIN review_progress p ON p.source_result_id=r.id
               WHERE r.user_id=? AND r.score<80
                 AND NOT EXISTS (
                   SELECT 1 FROM review_attempts retry WHERE retry.result_id=r.id
                 )
                 AND (r.kind='exam' OR p.completed_at IS NULL)""",
            (user["id"],),
        ).fetchone()[0]
        activity_days = [row[0] for row in conn.execute(
            """SELECT DISTINCT date(created_at,'unixepoch','localtime') day FROM results
               WHERE user_id=? UNION SELECT DISTINCT date(last_looked_at,'unixepoch','localtime')
               FROM dictionary_history WHERE user_id=? ORDER BY day DESC""",
            (user["id"], user["id"]),
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
    skill_scores = {"listening": [], "reading": [], "writing": [], "handwriting": []}
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
    today = time.strftime("%Y-%m-%d", time.localtime())
    streak = 0
    cursor = int(time.mktime(time.strptime(today, "%Y-%m-%d")))
    days = set(activity_days)
    while time.strftime("%Y-%m-%d", time.localtime(cursor)) in days:
        streak += 1
        cursor -= 86400
    averages = {key: round(sum(values) / len(values), 1) if values else 0
                for key, values in skill_scores.items()}
    return {
        "results": len(results),
        "average_score": round(sum(r["score"] for r in current_results) / len(current_results), 1) if current_results else 0,
        "needs_review": needs_review,
        "vocabulary_count": vocabulary_count,
        "streak": streak,
        "skill_scores": averages,
        "progress_percent": round(sum(r["score"] for r in current_results) / len(current_results), 1) if current_results else 0,
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
    except Exception:
        record_ai_usage(user["id"], "capability", "error")
        raise HTTPException(502, "AI chưa thể tạo báo cáo năng lực. Vui lòng thử lại.") from None
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
def audit_logs(limit: int = Query(default=100, ge=1, le=500), offset: int = Query(default=0, ge=0), user=Depends(admin_user)):
    with database() as conn:
        return [dict(row) for row in conn.execute("SELECT a.*,u.name FROM audit_logs a JOIN users u ON u.id=a.actor_id ORDER BY a.id DESC LIMIT ? OFFSET ?", (limit, offset))]


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


ADMIN_DIR = Path(__file__).resolve().parent.parent / "admin"
WEB_DIR = Path(os.environ["WEB_APP_DIR"]).resolve() if os.getenv("WEB_APP_DIR") else None
app.mount("/admin/assets", StaticFiles(directory=ADMIN_DIR), name="admin-assets")
app.mount("/media", StaticFiles(directory=Path(__file__).parent / "media", check_dir=False), name="media")


@app.get("/admin", include_in_schema=False)
@app.get("/admin/", include_in_schema=False)
def admin_page():
    # The shell shows login only. Every administrative data route requires admin_user.
    if WEB_DIR is not None:
        html = (ADMIN_DIR / "index.html").read_text(encoding="utf-8")
        return HTMLResponse(html.replace('<head>', '<head><script>window.HANZIGO_UNIFIED_WEB=true;</script>'))
    return FileResponse(ADMIN_DIR / "index.html")


@app.get("/review", include_in_schema=False)
def learner_review_page():
    return FileResponse(ADMIN_DIR / "review.html")


if WEB_DIR is not None:
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="learner-web")
