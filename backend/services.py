"""Server-side contracts for Trung/Kiệt. Never accept a client-supplied score."""
import math
import os
import time
from collections.abc import Callable
from typing import Any

from fastapi import HTTPException

from database import database


def ai_settings():
    """Credentials returned here stay on the server, not in HTTP responses/logs."""
    with database() as conn:
        settings = dict(conn.execute("SELECT * FROM ai_config WHERE id=1").fetchone())
    key = os.getenv("AI_API_KEY", "").strip()
    if not settings["enabled"] or not key or settings["model"] == "configure-your-model":
        raise HTTPException(503, "AI chưa được cấu hình. Vui lòng thử lại sau.")
    settings["api_key"] = key
    return settings


def record_ai_usage(user_id: int, module: str, status: str):
    with database() as conn:
        conn.execute("INSERT INTO ai_usage(user_id,module,status,created_at) VALUES(?,?,?,?)",
                     (user_id, module, status, int(time.time())))


def grade_with_ai(user_id: int, kind: str, content: str, provider: Callable[[dict, str], dict[str, Any]]):
    """Invoke a trusted provider adapter with a timeout, supplied by the AI module.

    provider(settings, content) must return {score: 0..100, feedback: str}.
    The caller passes user_id from current_user, never from the request body.
    Transport/provider failures are sanitized; no exception text or key is logged.
    """
    if kind not in ("handwriting", "writing") or not content.strip() or len(content) > 100_000:
        raise HTTPException(422, "Loại bài hoặc nội dung không hợp lệ")
    try:
        settings = ai_settings()
    except HTTPException:
        record_ai_usage(user_id, kind, "error")
        raise
    try:
        output = provider(settings, content)
        score = float(output["score"])
        feedback = output["feedback"]
        if not math.isfinite(score) or not 0 <= score <= 100 or not isinstance(feedback, str) or len(feedback) > 10000:
            raise ValueError("Invalid grade")
    except Exception:
        record_ai_usage(user_id, kind, "error")
        raise HTTPException(502, "Dịch vụ AI chưa trả được kết quả hợp lệ. Vui lòng thử lại.") from None
    with database() as conn:
        rid = conn.execute("INSERT INTO results(user_id,kind,content,score,original_score,feedback,graded_by,created_at) VALUES(?,?,?,?,?,?,'ai',?)",
                           (user_id, kind, content, score, score, feedback, int(time.time()))).lastrowid
        conn.execute("INSERT INTO ai_usage(user_id,module,status,created_at) VALUES(?,?,'success',?)",
                     (user_id, kind, int(time.time())))
        return dict(conn.execute("SELECT * FROM results WHERE id=?", (rid,)).fetchone())
