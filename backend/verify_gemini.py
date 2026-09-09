"""Perform a small, non-persistent Gemini connection check."""
import json
import sys

from services import ai_settings, gemini_exam_provider, gemini_handwriting_provider


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
    handwriting = json.dumps({
        "target": "一",
        "standard_strokes": [[{"x": 180, "y": 512}, {"x": 840, "y": 512}]],
        "submitted_strokes": [[{"x": 200, "y": 520}, {"x": 820, "y": 510}]],
    }, ensure_ascii=False)
    writing_result = gemini_handwriting_provider(settings, handwriting)
    writing_score = writing_result.get("score")
    if not isinstance(writing_score, (int, float)) or not isinstance(
            writing_result.get("feedback"), str):
        raise SystemExit("Gemini chưa chấm được ảnh viết tay.")
    print(f"Kết nối Gemini thành công. Bài Đọc: {score}; Viết tay: {writing_score}.")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    verify()
