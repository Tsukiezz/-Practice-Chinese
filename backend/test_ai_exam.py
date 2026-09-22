import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

from fastapi.testclient import TestClient

import database as storage
from main import app
from ai_exam import init_ai_exam_tables


class AIExamTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_db = storage.DB_PATH
        storage.DB_PATH = Path(self.temp.name) / "test.db"
        self.client = TestClient(app)
        self.client.__enter__()

        # Register Student 1
        r1 = self.client.post("/api/auth/register", json={
            "name": "Học viên A",
            "email": "student_a@example.test",
            "password": "Password123!"
        })
        self.assertEqual(r1.status_code, 201)
        self.token_a = r1.json()["token"]
        self.headers_a = {"Authorization": "Bearer " + self.token_a}

        # Register Student 2
        r2 = self.client.post("/api/auth/register", json={
            "name": "Học viên B",
            "email": "student_b@example.test",
            "password": "Password123!"
        })
        self.assertEqual(r2.status_code, 201)
        self.token_b = r2.json()["token"]
        self.headers_b = {"Authorization": "Bearer " + self.token_b}

        # Seed sample vocabulary into test DB
        with storage.database() as conn:
            init_ai_exam_tables(conn)
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS vocabulary (
                    id INTEGER PRIMARY KEY, hanzi TEXT NOT NULL UNIQUE, pinyin TEXT NOT NULL,
                    meaning TEXT NOT NULL, hsk INTEGER NOT NULL, example TEXT NOT NULL DEFAULT '',
                    audio_url TEXT NOT NULL DEFAULT '', strokes_json TEXT NOT NULL DEFAULT '[]', version INTEGER NOT NULL DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS vocabulary_topics (
                    word_id INTEGER NOT NULL, topic TEXT NOT NULL, PRIMARY KEY(word_id, topic)
                );
                INSERT OR IGNORE INTO vocabulary(id, hanzi, pinyin, meaning, hsk, example) VALUES
                (1, '你好', 'nǐ hǎo', 'xin chào', 1, '你好，我是李明。'),
                (2, '谢谢', 'xiè xie', 'cảm ơn', 1, '谢谢你的帮助。'),
                (3, '再见', 'zài jiàn', 'tạm biệt', 1, '明天见，再见！'),
                (4, '同学', 'tóng xué', 'bạn học', 1, '他是我的同学。'),
                (5, '老师', 'lǎo shī', 'thầy cô giáo', 1, '王老师好！'),
                (6, '苹果', 'píng guǒ', 'quả táo', 1, '我喜欢吃苹果。'),
                (7, '学校', 'xué xiào', 'trường học', 1, '我们的学校很大。'),
                (8, '学习', 'xué xí', 'học tập', 1, '我爱学习汉语。');

                INSERT OR IGNORE INTO vocabulary_topics(word_id, topic) VALUES
                (1, 'communication'), (2, 'communication'), (3, 'communication'),
                (4, 'school'), (5, 'school'), (6, 'food'), (7, 'school'), (8, 'school');
            """)

    def tearDown(self):
        self.client.__exit__(None, None, None)
        storage.DB_PATH = self.old_db
        self.temp.cleanup()

    def test_exam_generation_and_time_rule(self):
        """Test question count options and 1 minute per question duration rule."""
        res = self.client.post("/api/me/ai-exams/generate", headers=self.headers_a, json={
            "question_count": 5,
            "content_type": "random"
        })
        self.assertEqual(res.status_code, 201, res.text)
        data = res.json()

        # 1 minute per question rule
        self.assertEqual(data["question_count"], 5)
        self.assertEqual(data["duration_minutes"], 5)
        self.assertEqual(data["duration_seconds"], 300)
        self.assertEqual(data["status"], "pending")
        self.assertEqual(len(data["questions"]), 5)

        for q in data["questions"]:
            self.assertTrue(q["id"].startswith("q"))
            self.assertTrue(bool(q["prompt"]))
            self.assertEqual(len(q["options"]), 4)
            self.assertTrue(bool(q["answer"]))
            self.assertTrue(bool(q["explanation"]))
            self.assertTrue(bool(q["correction"]))

    def test_exam_vocabulary_customization(self):
        """Test creating exam with vocabulary and HSK level / topic."""
        res = self.client.post("/api/me/ai-exams/generate", headers=self.headers_a, json={
            "question_count": 4,
            "content_type": "vocabulary",
            "hsk_level": 1,
            "topic": "school"
        })
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertIn("Từ vựng", data["title"])
        self.assertEqual(data["duration_minutes"], 4)
        self.assertEqual(len(data["questions"]), 4)

    def test_student_isolation(self):
        """Test exam is strictly private to the student who requested it."""
        # Student A creates an exam
        res_create = self.client.post("/api/me/ai-exams/generate", headers=self.headers_a, json={
            "question_count": 3,
            "content_type": "random"
        })
        exam_id = res_create.json()["id"]

        # Student A sees it in their pending list
        list_a = self.client.get("/api/me/ai-exams", headers=self.headers_a).json()
        self.assertTrue(any(e["id"] == exam_id for e in list_a["pending"]))

        # Student B sees NOTHING in their list
        list_b = self.client.get("/api/me/ai-exams", headers=self.headers_b).json()
        self.assertEqual(len(list_b["pending"]), 0)
        self.assertEqual(len(list_b["completed"]), 0)

        # Student B tries to access Student A's exam -> 404
        res_b = self.client.get(f"/api/me/ai-exams/{exam_id}", headers=self.headers_b)
        self.assertEqual(res_b.status_code, 404)

        # Student B cannot submit Student A's exam -> 404
        res_sub_b = self.client.post(f"/api/me/ai-exams/{exam_id}/submit", headers=self.headers_b, json={"answers": {}})
        self.assertEqual(res_sub_b.status_code, 404)

    def test_do_later_and_do_now_flow(self):
        """Test that generated exams stay pending for 'Làm sau' and can be fetched anytime."""
        res = self.client.post("/api/me/ai-exams/generate", headers=self.headers_a, json={
            "question_count": 5,
            "content_type": "random"
        })
        exam_id = res.json()["id"]

        # Student chooses 'Làm sau' -> Exam remains pending
        detail = self.client.get(f"/api/me/ai-exams/{exam_id}", headers=self.headers_a).json()
        self.assertEqual(detail["status"], "pending")
        self.assertEqual(len(detail["questions"]), 5)

    def test_submit_and_ai_grading_with_corrections(self):
        """Test submission, automated grading, identifying wrong answers, and providing corrections."""
        res_create = self.client.post("/api/me/ai-exams/generate", headers=self.headers_a, json={
            "question_count": 4,
            "content_type": "random"
        })
        exam = res_create.json()
        exam_id = exam["id"]
        questions = exam["questions"]

        # Prepare answers: 2 correct, 2 wrong
        answers = {
            questions[0]["id"]: questions[0]["answer"],  # correct
            questions[1]["id"]: questions[1]["answer"],  # correct
            questions[2]["id"]: "Z. Đáp án sai",          # incorrect
            questions[3]["id"]: "Sai hoàn toàn"           # incorrect
        }

        res_submit = self.client.post(f"/api/me/ai-exams/{exam_id}/submit", headers=self.headers_a, json={
            "answers": answers
        })
        self.assertEqual(res_submit.status_code, 200, res_submit.text)
        result = res_submit.json()

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["score"], 50.0)  # 2/4 = 50%
        feedback = result["feedback"]
        self.assertEqual(feedback["correct_count"], 2)
        self.assertEqual(feedback["total_questions"], 4)

        # Verify corrections for wrong answers
        wrong_details = [d for d in feedback["details"] if not d["is_correct"]]
        self.assertEqual(len(wrong_details), 2)
        for w in wrong_details:
            self.assertTrue(bool(w["correct_answer"]))
            self.assertTrue(bool(w["correction"]))
            self.assertTrue(bool(w["explanation"]))

        # Check that exam is now listed under 'completed'
        my_exams = self.client.get("/api/me/ai-exams", headers=self.headers_a).json()
        self.assertEqual(len(my_exams["pending"]), 0)
        self.assertEqual(len(my_exams["completed"]), 1)
        self.assertEqual(my_exams["completed"][0]["score"], 50.0)

        # Cannot submit again
        res_again = self.client.post(f"/api/me/ai-exams/{exam_id}/submit", headers=self.headers_a, json={"answers": {}})
        self.assertEqual(res_again.status_code, 400)

    def test_each_generation_produces_fresh_content(self):
        """Test that multiple generations create different exams."""
        res1 = self.client.post("/api/me/ai-exams/generate", headers=self.headers_a, json={
            "question_count": 3,
            "content_type": "random"
        })
        res2 = self.client.post("/api/me/ai-exams/generate", headers=self.headers_a, json={
            "question_count": 3,
            "content_type": "random"
        })
        self.assertNotEqual(res1.json()["id"], res2.json()["id"])
