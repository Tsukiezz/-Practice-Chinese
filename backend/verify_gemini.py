"""Perform a small, non-persistent Gemini connection check for AI exam grading."""
import sys

import json

from services import ai_settings, gemini_exam_provider


def verify() -> None:
    sample = json.dumps(
        {
            "exam_title": "Kiểm tra kết nối Gemini",
            "questions": [
                {
                    "id": "probe-1",
                    "section": "reading",
                    "prompt": "一 nghĩa là gì?",
                    "options": ["một", "hai"],
                    "answer": "một",
                    "submitted_answer": "một",
                }
            ],
        },
        ensure_ascii=False,
    )
    settings = ai_settings()
    result = gemini_exam_provider(settings, sample)
    score = result.get("score")
    feedback = result.get("feedback")
    if not isinstance(score, (int, float)) or not isinstance(feedback, str):
        raise SystemExit("Gemini trả dữ liệu không đúng định dạng.")
    if not isinstance(result.get("review_items"), list):
        raise SystemExit("Gemini chưa trả lời giải chi tiết.")
    section_scores = result.get("section_scores")
    if not isinstance(section_scores, dict) or not isinstance(section_scores.get("reading"), (int, float)):
        raise SystemExit("Gemini chưa trả điểm theo từng kỹ năng.")
    print(f"Kết nối Gemini thành công. Bài Đọc: {score}. Luyện nét chạy offline.")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    verify()
