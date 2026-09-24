"""AI Examination Generator and Auto-Grader for HanziGo learners."""
import json
import random
import time
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from ai_errors import ai_http_error
from database import database
from services import _decode_gemini_candidate, _post_gemini, ai_settings, record_ai_usage

DATA_DIR = Path(__file__).parent / "data"
TOPICS_FILE = DATA_DIR / "topics.json"


def load_topics():
    if TOPICS_FILE.exists():
        return json.loads(TOPICS_FILE.read_text(encoding="utf-8"))
    return {}


def init_ai_exam_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS student_ai_exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            content_type TEXT NOT NULL,
            hsk_level INTEGER,
            topic TEXT,
            question_count INTEGER NOT NULL,
            duration_minutes INTEGER NOT NULL,
            questions_json TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            score REAL,
            user_answers_json TEXT,
            ai_feedback_json TEXT,
            submitted_at INTEGER,
            created_at INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_student_ai_exams_user ON student_ai_exams(user_id, status);
    """)


class GenerateAIExamRequest(BaseModel):
    question_count: int = Field(default=40, ge=1, le=50)
    content_type: str = Field(default="random")  # 'random' or 'vocabulary'
    hsk_level: int | None = Field(default=None, ge=1, le=6)
    topic: str | None = Field(default=None, max_length=50)


class SubmitAIExamRequest(BaseModel):
    answers: dict[str, str] = Field(default_factory=dict)


def ensure_hsk_standard_exams(conn, user_id: int):
    """Ensure the student has official 40-question mock exams for HSK 1 through HSK 6 (40 minutes each)."""
    now = int(time.time())
    for lvl in range(1, 7):
        exists = conn.execute(
            """SELECT id FROM student_ai_exams
               WHERE user_id = ? AND hsk_level = ? AND content_type = 'standard_hsk' AND question_count = 40""",
            (user_id, lvl)
        ).fetchone()
        if not exists:
            questions = generate_questions_from_db(conn, 40, "vocabulary", lvl, None)
            title = f"Đề thi thử HSK {lvl} Chuẩn (40 câu · 40 phút)"
            conn.execute(
                """INSERT INTO student_ai_exams (
                    user_id, title, content_type, hsk_level, topic,
                    question_count, duration_minutes, questions_json,
                    status, created_at
                ) VALUES (?, ?, 'standard_hsk', ?, '', 40, 40, ?, 'pending', ?)""",
                (user_id, title, lvl, json.dumps(questions, ensure_ascii=False), now)
            )


def generate_questions_from_db(conn, count: int, content_type: str, hsk_level: int | None, topic: str | None) -> list[dict]:
    """Dynamically generate diverse, realistic Chinese exam questions from local 5000 HSK vocabulary."""
    base_query = "SELECT v.id, v.hanzi, v.pinyin, v.meaning, v.hsk, v.example FROM vocabulary v"
    joins = []
    conditions = []
    params = []

    if topic:
        joins.append("JOIN vocabulary_topics t ON t.word_id = v.id")
        conditions.append("t.topic = ?")
        params.append(topic)

    if hsk_level:
        conditions.append("v.hsk = ?")
        params.append(hsk_level)

    query_str = base_query
    if joins:
        query_str += " " + " ".join(joins)
    if conditions:
        query_str += " WHERE " + " AND ".join(conditions)

    rows = conn.execute(query_str, params).fetchall()
    if not rows or len(rows) < 4:
        # Fallback to general vocabulary
        rows = conn.execute("SELECT id, hanzi, pinyin, meaning, hsk, example FROM vocabulary ORDER BY RANDOM() LIMIT 200").fetchall()

    word_list = [dict(r) for r in rows]
    random.shuffle(word_list)

    # Distractor pool
    distractor_pool = conn.execute("SELECT hanzi, pinyin, meaning, hsk FROM vocabulary ORDER BY RANDOM() LIMIT 300").fetchall()
    distractor_list = [dict(r) for r in distractor_pool]

    selected_words = list(word_list[:count])
    while len(selected_words) < count and word_list:
        needed = count - len(selected_words)
        selected_words.extend(word_list[:needed])
    questions = []

    templates = ["hanzi_to_meaning", "meaning_to_hanzi", "hanzi_to_pinyin", "cloze"]

    for idx, target in enumerate(selected_words):
        qid = f"q{idx + 1}"
        template = random.choice(templates)

        # Find 3 distractor words with same HSK or random
        distractors = [d for d in distractor_list if d["hanzi"] != target["hanzi"]]
        same_hsk = [d for d in distractors if d["hsk"] == target["hsk"]]
        if len(same_hsk) >= 3:
            distractors = random.sample(same_hsk, 3)
        else:
            distractors = random.sample(distractors, 3)

        if template == "hanzi_to_meaning":
            prompt = f"Chọn nghĩa tiếng Việt chính xác của từ: {target['hanzi']}"
            pinyin = target["pinyin"]
            correct_val = target["meaning"].split(";")[0].strip()
            distractor_vals = [d["meaning"].split(";")[0].strip() for d in distractors]
            all_choices = [correct_val] + distractor_vals
            random.shuffle(all_choices)
            letter_idx = all_choices.index(correct_val)
            letters = ["A", "B", "C", "D"]
            options = [f"{letters[i]}. {val}" for i, val in enumerate(all_choices)]
            correct_answer = f"{letters[letter_idx]}. {correct_val}"
            explanation = f"Từ '{target['hanzi']}' (phiên âm: {target['pinyin']}) có nghĩa là '{target['meaning']}'."
            correction = f"Đáp án đúng là {correct_answer}. Các phương án khác mang nghĩa: " + ", ".join(
                [f"'{d['hanzi']}' ({d['meaning']})" for d in distractors]
            ) + "."

        elif template == "meaning_to_hanzi":
            prompt = f"Từ tiếng Trung nào dưới đây mang nghĩa: \"{target['meaning'].split(';')[0].strip()}\"?"
            pinyin = target["pinyin"]
            correct_val = f"{target['hanzi']} ({target['pinyin']})"
            distractor_vals = [f"{d['hanzi']} ({d['pinyin']})" for d in distractors]
            all_choices = [correct_val] + distractor_vals
            random.shuffle(all_choices)
            letter_idx = all_choices.index(correct_val)
            letters = ["A", "B", "C", "D"]
            options = [f"{letters[i]}. {val}" for i, val in enumerate(all_choices)]
            correct_answer = f"{letters[letter_idx]}. {correct_val}"
            explanation = f"Nghĩa '{target['meaning']}' trong tiếng Trung là '{target['hanzi']}', phát âm là '{target['pinyin']}'."
            correction = f"Đáp án đúng là {correct_answer}. Sửa lại: " + "; ".join(
                [f"'{d['hanzi']}' nghĩa là {d['meaning']}" for d in distractors]
            ) + "."

        elif template == "hanzi_to_pinyin":
            prompt = f"Phiên âm Pinyin chính xác của chữ '{target['hanzi']}' ({target['meaning'].split(';')[0].strip()}) là gì?"
            pinyin = target["pinyin"]
            correct_val = target["pinyin"]
            distractor_vals = [d["pinyin"] for d in distractors]
            all_choices = [correct_val] + distractor_vals
            random.shuffle(all_choices)
            letter_idx = all_choices.index(correct_val)
            letters = ["A", "B", "C", "D"]
            options = [f"{letters[i]}. {val}" for i, val in enumerate(all_choices)]
            correct_answer = f"{letters[letter_idx]}. {correct_val}"
            explanation = f"Chữ Hán '{target['hanzi']}' được phiên âm chuẩn là '{target['pinyin']}', nghĩa là '{target['meaning']}'."
            correction = f"Đáp án đúng là {correct_answer}. Chú ý cách phát âm và thanh điệu chuẩn của từ '{target['hanzi']}' là '{target['pinyin']}'."

        else:  # cloze or context
            example = target.get("example", "").strip()
            if example and target["hanzi"] in example:
                blank_sentence = example.replace(target["hanzi"], "____", 1)
                prompt = f"Chọn từ thích hợp điền vào chỗ trống: {blank_sentence}"
            else:
                prompt = f"Chọn từ thích hợp để hoàn thiện ý nghĩa: \"____ ({target['meaning'].split(';')[0].strip()})\""
            pinyin = target["pinyin"]
            correct_val = target["hanzi"]
            distractor_vals = [d["hanzi"] for d in distractors]
            all_choices = [correct_val] + distractor_vals
            random.shuffle(all_choices)
            letter_idx = all_choices.index(correct_val)
            letters = ["A", "B", "C", "D"]
            options = [f"{letters[i]}. {val} ({all_choices[i]})" if "(" not in val else f"{letters[i]}. {val}" for i, val in enumerate(all_choices)]
            # Re-normalize options
            options = [f"{letters[i]}. {val}" for i, val in enumerate(all_choices)]
            correct_answer = f"{letters[letter_idx]}. {correct_val}"
            explanation = f"Từ cần điền là '{target['hanzi']}' ({target['pinyin']}) mang nghĩa '{target['meaning']}' phù hợp nhất với ngữ cảnh."
            correction = f"Đáp án đúng là {correct_answer}. Hãy phân biệt rõ nghĩa của các từ trong lựa chọn: " + ", ".join(
                [f"'{d['hanzi']}' ({d['pinyin']}: {d['meaning']})" for d in distractors]
            ) + "."

        questions.append({
            "id": qid,
            "prompt": prompt,
            "pinyin": pinyin,
            "options": options,
            "answer": correct_answer,
            "explanation": explanation,
            "correction": correction,
        })

    return questions


def generate_questions_with_gemini(user_id: int, count: int, content_type: str, hsk_level: int | None, topic: str | None) -> list[dict] | None:
    """Attempt generating questions using Gemini AI."""
    try:
        settings = ai_settings()
    except Exception:
        return None

    topics_map = load_topics()
    topic_name = topics_map.get(topic, topic) if topic else ""

    topic_desc = []
    if content_type == "vocabulary":
        if hsk_level:
            topic_desc.append(f"Cấp độ HSK {hsk_level}")
        if topic_name:
            topic_desc.append(f"Chủ đề từ vựng: {topic_name}")
        if not topic_desc:
            topic_desc.append("Từ vựng tiếng Trung ứng dụng HSK 1 - HSK 4")
    else:
        topic_desc.append("Kiến thức tiếng Trung tổng hợp ngẫu nhiên (từ vựng, ngữ pháp, đặt câu, đọc hiểu ngắn)")

    prompt = (
        f"Hãy tạo 1 đề thi trắc nghiệm tiếng Trung mới gồm đúng {count} câu hỏi trắc nghiệm khách quan.\n"
        f"Nội dung yêu cầu: {', '.join(topic_desc)}.\n"
        f"Mỗi câu hỏi phải độc đáo, không trùng lặp, gồm:\n"
        "- prompt: Câu hỏi hoặc câu có chỗ trống cần điền bằng tiếng Trung.\n"
        "- pinyin: Phiên âm Pinyin kèm dấu thanh điệu chuẩn cho phần tiếng Trung trong câu hỏi.\n"
        "- options: Mảng đúng 4 lựa chọn có tiền tố 'A. ', 'B. ', 'C. ', 'D. '.\n"
        "- answer: Đáp án đúng, khớp chính xác 100% với một trong 4 options (ví dụ: 'A. 同学').\n"
        "- explanation: Giải thích chi tiết bằng tiếng Việt tại sao đáp án đó đúng (nghĩa từ, ngữ pháp, ngữ cảnh).\n"
        "- correction: Mục 'Sửa thành cho đúng' bằng tiếng Việt, phân tích vì sao các phương án khác sai hoặc cách nhớ để không bị nhầm lẫn.\n"
    )

    schema = {
        "type": "object",
        "properties": {
            "questions": {
                "type": "array",
                "minItems": count,
                "maxItems": count,
                "items": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string"},
                        "pinyin": {"type": "string"},
                        "options": {
                            "type": "array",
                            "minItems": 4,
                            "maxItems": 4,
                            "items": {"type": "string"},
                        },
                        "answer": {"type": "string"},
                        "explanation": {"type": "string"},
                        "correction": {"type": "string"},
                    },
                    "required": ["prompt", "pinyin", "options", "answer", "explanation", "correction"],
                },
            }
        },
        "required": ["questions"],
    }

    try:
        model = quote(settings["model"], safe="._-")
        response = _post_gemini(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            headers={"x-goog-api-key": settings["api_key"]},
            json={
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "systemInstruction": {
                    "parts": [{
                        "text": "Bạn là chuyên gia khảo thí tiếng Trung HSK hàng đầu. Luôn tạo đề thi mới mẻ, hấp dẫn, chuẩn xác và sinh JSON đúng định dạng."
                    }]
                },
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "responseSchema": schema,
                    "temperature": 0.7,
                    "maxOutputTokens": 8192,
                },
            },
            timeout=30.0,
        )
        response.raise_for_status()
        candidate = _decode_gemini_candidate(response)
        raw_questions = candidate.get("questions", [])
        if len(raw_questions) != count:
            return None

        result = []
        for i, q in enumerate(raw_questions):
            result.append({
                "id": f"q{i + 1}",
                "prompt": q["prompt"].strip(),
                "pinyin": q.get("pinyin", "").strip(),
                "options": [opt.strip() for opt in q["options"]],
                "answer": q["answer"].strip(),
                "explanation": q.get("explanation", "").strip(),
                "correction": q.get("correction", "").strip(),
            })
        record_ai_usage(user_id, "ai_exam_generate", "success")
        return result
    except Exception as exc:
        record_ai_usage(user_id, "ai_exam_generate", "error")
        return None


def grade_ai_exam(questions: list[dict], user_answers: dict[str, str]) -> tuple[float, list[dict], str]:
    """Grade submission, identify errors, produce scores and detailed corrections."""
    total = len(questions)
    if total == 0:
        return 0.0, [], "Đề thi không có câu hỏi."

    correct_count = 0
    details = []

    for q in questions:
        qid = q["id"]
        correct_ans = q["answer"].strip()
        user_ans = user_answers.get(qid, "").strip()

        # Check equivalence (handle "A. ..." vs "A" or exact match)
        is_correct = False
        if user_ans:
            if user_ans.lower() == correct_ans.lower():
                is_correct = True
            elif user_ans.split(".", 1)[0].strip().upper() == correct_ans.split(".", 1)[0].strip().upper():
                is_correct = True
            elif user_ans.split(".", 1)[-1].strip() == correct_ans.split(".", 1)[-1].strip():
                is_correct = True

        if is_correct:
            correct_count += 1

        details.append({
            "id": qid,
            "prompt": q["prompt"],
            "pinyin": q.get("pinyin", ""),
            "options": q["options"],
            "user_answer": user_ans if user_ans else "(Chưa làm)",
            "correct_answer": correct_ans,
            "is_correct": is_correct,
            "explanation": q.get("explanation", ""),
            "correction": q.get("correction", ""),
        })

    score = round((correct_count / total) * 100, 1)
    wrong_count = total - correct_count

    if score >= 90:
        evaluation = f"Xuất sắc! Bạn làm đúng {correct_count}/{total} câu ({score}/100 điểm)."
    elif score >= 70:
        evaluation = f"Khá tốt! Bạn làm đúng {correct_count}/{total} câu ({score}/100 điểm). Có {wrong_count} câu cần xem lại."
    elif score >= 50:
        evaluation = f"Đạt yêu cầu. Bạn làm đúng {correct_count}/{total} câu ({score}/100 điểm). Hãy xem kỹ phần 'Sửa thành cho đúng'."
    else:
        evaluation = f"Cần cố gắng thêm. Bạn làm đúng {correct_count}/{total} câu ({score}/100 điểm). Hãy xem chi tiết giải thích và ôn tập lại."

    return score, details, evaluation


def register_ai_exam_routes(app, current_user):
    """Register learner AI Exam API routes."""

    @app.get("/api/ai-exams/topics")
    def get_topics():
        topics_map = load_topics()
        return [{"id": k, "label": v} for k, v in topics_map.items()]

    @app.post("/api/me/ai-exams/generate", status_code=201)
    def generate_exam(body: GenerateAIExamRequest, user=Depends(current_user)):
        topics_map = load_topics()
        topic_name = topics_map.get(body.topic, body.topic) if body.topic else None

        # Build dynamic title
        if body.content_type == "vocabulary":
            if body.hsk_level and topic_name:
                title = f"Đề thi Từ vựng HSK {body.hsk_level} · {topic_name} ({body.question_count} câu)"
            elif body.hsk_level:
                title = f"Đề thi Từ vựng HSK {body.hsk_level} ({body.question_count} câu)"
            elif topic_name:
                title = f"Đề thi Từ vựng · {topic_name} ({body.question_count} câu)"
            else:
                title = f"Đề thi Từ vựng tiếng Trung ({body.question_count} câu)"
        else:
            title = f"Đề thi Tổng hợp Ngẫu nhiên ({body.question_count} câu)"

        # Time rule: 1 minute per question
        duration_minutes = body.question_count * 1

        # Attempt Gemini generation first
        questions = generate_questions_with_gemini(
            user["id"], body.question_count, body.content_type, body.hsk_level, body.topic
        )

        # Fallback to local 5,000-word HSK corpus if Gemini is not configured/fails
        if not questions or len(questions) != body.question_count:
            with database() as conn:
                questions = generate_questions_from_db(
                    conn, body.question_count, body.content_type, body.hsk_level, body.topic
                )

        now = int(time.time())
        with database() as conn:
            exam_id = conn.execute(
                """INSERT INTO student_ai_exams (
                    user_id, title, content_type, hsk_level, topic,
                    question_count, duration_minutes, questions_json,
                    status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)""",
                (
                    user["id"], title, body.content_type, body.hsk_level, body.topic or "",
                    body.question_count, duration_minutes, json.dumps(questions, ensure_ascii=False),
                    now
                )
            ).lastrowid

        return {
            "id": exam_id,
            "title": title,
            "content_type": body.content_type,
            "hsk_level": body.hsk_level,
            "topic": body.topic,
            "question_count": body.question_count,
            "duration_minutes": duration_minutes,
            "duration_seconds": duration_minutes * 60,
            "questions": questions,
            "status": "pending",
            "created_at": now,
        }

    @app.get("/api/me/ai-exams")
    def list_exams(user=Depends(current_user), include_standard: bool = Query(default=False)):
        with database() as conn:
            if include_standard:
                ensure_hsk_standard_exams(conn, user["id"])
            rows = conn.execute(
                """SELECT id, title, content_type, hsk_level, topic,
                          question_count, duration_minutes, status, score,
                          created_at, submitted_at
                   FROM student_ai_exams
                   WHERE user_id = ?
                   ORDER BY 
                     CASE WHEN content_type = 'standard_hsk' THEN 0 ELSE 1 END,
                     hsk_level ASC,
                     created_at DESC""",
                (user["id"],)
            ).fetchall()

        pending = []
        completed = []
        standard_hsk = []
        for r in rows:
            item = dict(r)
            if item.get("content_type") == "standard_hsk":
                standard_hsk.append(item)
                if not include_standard:
                    continue
            if item["status"] == "completed":
                completed.append(item)
            else:
                pending.append(item)

        return {"pending": pending, "completed": completed, "standard_hsk": standard_hsk}

    @app.get("/api/me/ai-exams/standard-presets")
    def get_standard_presets(user=Depends(current_user)):
        with database() as conn:
            ensure_hsk_standard_exams(conn, user["id"])
            rows = conn.execute(
                """SELECT id, title, content_type, hsk_level, topic,
                          question_count, duration_minutes, status, score,
                          created_at, submitted_at
                   FROM student_ai_exams
                   WHERE user_id = ? AND content_type = 'standard_hsk'
                   ORDER BY hsk_level ASC""",
                (user["id"],)
            ).fetchall()
            return [dict(r) for r in rows]

    @app.get("/api/me/ai-exams/{exam_id}")
    def get_exam(exam_id: int, user=Depends(current_user)):
        with database() as conn:
            row = conn.execute(
                """SELECT * FROM student_ai_exams WHERE id = ? AND user_id = ?""",
                (exam_id, user["id"])
            ).fetchone()

        if not row:
            raise HTTPException(404, "Không tìm thấy đề thi hoặc bạn không có quyền truy cập.")

        exam = dict(row)
        exam["questions"] = json.loads(exam.pop("questions_json"))
        exam["duration_seconds"] = exam["duration_minutes"] * 60
        if exam["user_answers_json"]:
            exam["user_answers"] = json.loads(exam.pop("user_answers_json"))
        else:
            exam["user_answers"] = {}
        if exam["ai_feedback_json"]:
            exam["ai_feedback"] = json.loads(exam.pop("ai_feedback_json"))
        else:
            exam["ai_feedback"] = None

        return exam

    @app.post("/api/me/ai-exams/{exam_id}/submit")
    def submit_exam(exam_id: int, body: SubmitAIExamRequest, user=Depends(current_user)):
        with database() as conn:
            row = conn.execute(
                """SELECT * FROM student_ai_exams WHERE id = ? AND user_id = ?""",
                (exam_id, user["id"])
            ).fetchone()

        if not row:
            raise HTTPException(404, "Không tìm thấy đề thi.")

        exam = dict(row)
        if exam["status"] == "completed":
            raise HTTPException(400, "Đề thi này đã được nộp trước đó.")

        questions = json.loads(exam["questions_json"])
        score, details, summary = grade_ai_exam(questions, body.answers)

        feedback_data = {
            "score": score,
            "correct_count": sum(1 for d in details if d["is_correct"]),
            "total_questions": len(questions),
            "summary": summary,
            "details": details,
        }

        now = int(time.time())
        with database() as conn:
            conn.execute(
                """UPDATE student_ai_exams
                   SET status = 'completed',
                       score = ?,
                       user_answers_json = ?,
                       ai_feedback_json = ?,
                       submitted_at = ?
                   WHERE id = ? AND user_id = ?""",
                (
                    score,
                    json.dumps(body.answers, ensure_ascii=False),
                    json.dumps(feedback_data, ensure_ascii=False),
                    now,
                    exam_id,
                    user["id"],
                )
            )

            # Record in global results table for dashboard progress
            conn.execute(
                """INSERT INTO results (
                    user_id, kind, content, score, original_score, feedback,
                    graded_by, created_at
                ) VALUES (?, 'exam', ?, ?, ?, ?, 'ai', ?)""",
                (
                    user["id"],
                    json.dumps({
                        "exam_id": exam_id,
                        "title": exam["title"],
                        "score": score,
                        "source": "student_ai_exam",
                    }, ensure_ascii=False),
                    score,
                    score,
                    summary,
                    now,
                )
            )

        return {
            "exam_id": exam_id,
            "status": "completed",
            "score": score,
            "feedback": feedback_data,
            "submitted_at": now,
        }

    @app.delete("/api/me/ai-exams/{exam_id}", status_code=204)
    def delete_exam(exam_id: int, user=Depends(current_user)):
        with database() as conn:
            res = conn.execute(
                "DELETE FROM student_ai_exams WHERE id = ? AND user_id = ?",
                (exam_id, user["id"])
            )
            if res.rowcount == 0:
                raise HTTPException(404, "Không tìm thấy đề thi để xóa.")
