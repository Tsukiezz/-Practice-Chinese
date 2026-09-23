"""UC-04 tests for Canvas and rubric-based essay questions in shared exams."""
import json
import os
from pathlib import Path
import unittest
import uuid
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from pydantic import ValidationError

import database as storage
from database import init_db
from main import app
from models import Question, Submission
from services import grade_essay_with_ai


ESSAY_OUTPUT = {
    "score": 1,  # The service must recompute this from the rubric criteria.
    "feedback": "Bài đúng chủ đề, cần tăng độ đa dạng từ vựng.",
    "details": {
        "grammar": {"score": 80, "feedback": "Ngữ pháp khá chính xác."},
        "vocabulary": {"score": 60, "feedback": "Từ vựng còn lặp."},
        "coherence": {"score": 70, "feedback": "Các ý nối tương đối rõ."},
        "task_fulfillment": {"score": 90, "feedback": "Đúng đề và đủ độ dài."},
        "strengths": ["Đúng chủ đề"],
        "weaknesses": ["Từ vựng lặp"],
    },
}


class EssayGradingUnitTest(unittest.TestCase):
    def setUp(self):
        self.old_path = storage.DB_PATH
        self.test_path = Path(__file__).with_name(
            f".test-essay-{uuid.uuid4().hex}.db")
        storage.DB_PATH = self.test_path
        init_db()
        with storage.database() as conn:
            conn.execute(
                """INSERT INTO users(
                       id,name,email,password_hash,salt,role,is_active,created_at
                   ) VALUES(1,'Student','student@example.test','hash','salt',
                            'student',1,1)""")
            conn.execute("UPDATE ai_config SET enabled=1,model='test-model'")

    def tearDown(self):
        storage.DB_PATH = self.old_path
        self.test_path.unlink(missing_ok=True)

    def test_rubric_score_cache_and_usage_are_deterministic(self):
        provider = Mock(return_value=ESSAY_OUTPUT)
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            first = grade_essay_with_ai(
                1, "Viết về gia đình", "Ít nhất 3 câu", "我家有三个人。", provider)
            second = grade_essay_with_ai(
                1, "Viết về gia đình", "Ít nhất 3 câu", "我家有三个人。", provider)

        self.assertEqual(first, second)
        self.assertEqual(first["score"], 74)
        provider.assert_called_once()
        with storage.database() as conn:
            usage = conn.execute(
                "SELECT module,status FROM ai_usage").fetchall()
            cache_row = conn.execute(
                "SELECT COUNT(*) FROM essay_cache").fetchone()
            assert cache_row is not None
            cache_count = cache_row[0]
        self.assertEqual([tuple(row) for row in usage],
                         [("essay_grading", "success")])
        self.assertEqual(cache_count, 1)

    def test_shared_models_keep_legacy_defaults_and_reject_bad_objects(self):
        legacy = Question(
            id="old", section="reading", prompt="一 nghĩa là gì?",
            options=["một", "hai"], answer="một")
        self.assertIsNone(legacy.question_type)
        self.assertEqual(legacy.weight, 1)
        with self.assertRaises(ValidationError):
            Submission(version=1, answers={
                "q1": {"kind": "hanzi_canvas", "strokes": [[{"x": 1}]]}  # type: ignore
            })
        with self.assertRaises(ValidationError):
            Submission(version=1, answers={
                "q1": {"kind": "essay", "text": "字" * 501}  # type: ignore
            })


class ExamWritingIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.old_path = storage.DB_PATH
        self.test_path = Path(__file__).with_name(
            f".test-exam-writing-{uuid.uuid4().hex}.db")
        storage.DB_PATH = self.test_path
        self.client = TestClient(app)
        self.client.__enter__()
        self.admin = self._register("admin@example.test", "Admin")
        self.student = self._register("student@example.test", "Student")
        with storage.database() as conn:
            conn.execute("UPDATE users SET role='admin' WHERE id=?",
                         (self.admin["user"]["id"],))
            conn.execute("UPDATE ai_config SET enabled=1,model='test-model'")
        self.admin_headers = {
            "Authorization": "Bearer " + self.admin["token"]}
        self.student_headers = {
            "Authorization": "Bearer " + self.student["token"]}

    def tearDown(self):
        self.client.__exit__(None, None, None)
        storage.DB_PATH = self.old_path
        self.test_path.unlink(missing_ok=True)

    def _register(self, email, name):
        response = self.client.post("/api/auth/register", json={
            "email": email, "name": name, "password": "Test-password-123"})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def _create_exam(self):
        stroke = [[{"x": 100, "y": 500}, {"x": 900, "y": 500}]]
        word = self.client.post("/api/admin/vocabulary",
            headers=self.admin_headers, json={
                "hanzi": "一", "pinyin": "yī", "meaning": "một",
                "hsk": 1, "strokes": stroke})
        self.assertEqual(word.status_code, 201, word.text)
        response = self.client.post("/api/admin/exams",
            headers=self.admin_headers, json={
                "title": "Test viết UC-04", "hsk": 1,
                "status": "published", "duration_minutes": 15,
                "questions": [
                    {"id": "canvas", "section": "writing",
                     "question_type": "hanzi_canvas", "weight": 1,
                     "prompt": "Viết chữ số một", "answer": "一"},
                    {"id": "essay", "section": "writing",
                     "question_type": "essay", "weight": 3,
                     "prompt": "Viết về gia đình", "answer": "Ít nhất 3 câu"},
                ]})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json(), stroke

    def test_weighted_submission_grades_canvas_offline_and_essay_with_cache(self):
        exam, stroke = self._create_exam()
        body = {"version": exam["version"], "answers": {
            "canvas": {"kind": "hanzi_canvas", "strokes": stroke},
            "essay": {"kind": "essay", "text": "我家有三个人。"},
        }}
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}), \
             patch("main.gemini_essay_provider",
                   return_value=ESSAY_OUTPUT) as provider:
            first = self.client.post(
                f"/api/exams/{exam['id']}/submit",
                headers=self.student_headers, json=body)
            second = self.client.post(
                f"/api/exams/{exam['id']}/submit",
                headers=self.student_headers, json=body)

        self.assertEqual(first.status_code, 201, first.text)
        self.assertEqual(second.status_code, 201, second.text)
        self.assertEqual(first.json()["score"], 80.5)
        snapshot = json.loads(first.json()["content"])
        self.assertEqual(snapshot["question_scores"]["canvas"]["score"], 100)
        self.assertEqual(snapshot["question_scores"]["essay"]["score"], 74)
        provider.assert_called_once()
        with storage.database() as conn:
            usage = conn.execute(
                "SELECT module,status FROM ai_usage").fetchall()
            rc_row = conn.execute(
                "SELECT COUNT(*) FROM results").fetchone()
            assert rc_row is not None
            result_count = rc_row[0]
        self.assertEqual([tuple(row) for row in usage],
                         [("essay_grading", "success")])
        self.assertEqual(result_count, 2)

    def test_canvas_endpoint_is_offline_and_invalid_answer_returns_422(self):
        exam, stroke = self._create_exam()
        with patch("main.gemini_essay_provider") as provider:
            grade = self.client.post(
                "/api/test-writing/grade-canvas",
                headers=self.student_headers,
                json={"target": "一", "strokes": stroke})
        self.assertEqual(grade.status_code, 200, grade.text)
        self.assertEqual(grade.json()["score"], 100)
        provider.assert_not_called()

        invalid = self.client.post(
            f"/api/exams/{exam['id']}/submit",
            headers=self.student_headers,
            json={"version": exam["version"], "answers": {
                "canvas": {"kind": "essay", "text": "sai kiểu"},
                "essay": {"kind": "essay", "text": "我家。"},
            }})
        self.assertEqual(invalid.status_code, 422, invalid.text)


if __name__ == "__main__":
    unittest.main()
