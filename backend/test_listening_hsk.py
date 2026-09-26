"""Unit tests for HSK 1 to HSK 6 listening exams."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

import database as storage
from listening_hsk_data import LISTENING_EXAMS_HSK1_6
from main import app


class ListeningHskTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_db = storage.DB_PATH
        storage.DB_PATH = Path(self.temp.name) / "test.db"
        storage.init_db()
        self.client = TestClient(app)
        self.client.__enter__()
        # Register a student
        resp = self.client.post("/api/auth/register", json={
            "name": "Học Viên Nghe",
            "email": "listening_student@example.test",
            "password": "password123",
        })
        self.token = resp.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def tearDown(self):
        self.client.__exit__(None, None, None)
        storage.DB_PATH = self.old_db
        self.temp.cleanup()

    def test_listening_data_completeness_hsk1_to_hsk6(self):
        """Validate structure and content of HSK 1 to HSK 6 listening dataset."""
        self.assertGreaterEqual(len(LISTENING_EXAMS_HSK1_6), 6)
        levels_seen = set()
        for exam in LISTENING_EXAMS_HSK1_6:
            self.assertIn("title", exam)
            self.assertIn("hsk", exam)
            self.assertIn("duration_minutes", exam)
            self.assertIn("questions", exam)
            self.assertGreaterEqual(exam["duration_minutes"], 5)
            self.assertIn(exam["hsk"], range(1, 7))
            levels_seen.add(exam["hsk"])
            self.assertGreaterEqual(len(exam["questions"]), 3)
            for q in exam["questions"]:
                self.assertEqual(q["section"], "listening")
                self.assertTrue(q["prompt"])
                self.assertGreaterEqual(len(q["options"]), 2)
                self.assertIn(q["answer"], q["options"])
                self.assertTrue(q["transcript"])
                self.assertTrue(q["explanation"])
                self.assertTrue(q["audio_url"])
        self.assertEqual(levels_seen, {1, 2, 3, 4, 5, 6})

    def test_seed_and_query_hsk1_to_hsk6(self):
        """Seed HSK 1-6 listening exams and verify query by HSK level via API."""
        with storage.database() as conn:
            storage.init_listening_exams(conn)

        for hsk in range(1, 7):
            resp = self.client.get(f"/api/exams?hsk={hsk}", headers=self.headers)
            self.assertEqual(resp.status_code, 200)
            exams = resp.json()
            self.assertGreaterEqual(len(exams), 1, f"Missing exam for HSK {hsk}")
            for exam in exams:
                self.assertEqual(exam["hsk"], hsk)
                self.assertEqual(exam["status"], "published")
                self.assertGreaterEqual(len(exam["questions"]), 1)
                for q in exam["questions"]:
                    self.assertEqual(q["section"], "listening")
                    self.assertTrue(q["audio_url"])
                    # Student view must NOT leak answers or transcripts
                    self.assertNotIn("answer", q)
                    self.assertNotIn("transcript", q)

    def test_submit_listening_exam_and_get_results(self):
        """Submit answers to an HSK listening exam and check scoring & review."""
        with storage.database() as conn:
            storage.init_listening_exams(conn)

        # Get HSK 1 listening exam
        exams = self.client.get("/api/exams?hsk=1", headers=self.headers).json()
        exam = exams[0]
        exam_id = exam["id"]
        q_ids = [q["id"] for q in exam["questions"]]

        # Submit perfect answers based on dataset
        raw_exam = [e for e in LISTENING_EXAMS_HSK1_6 if e["hsk"] == 1][0]
        correct_answers = {q["id"]: q["answer"] for q in raw_exam["questions"]}

        from unittest.mock import patch

        with patch("main.grade_listening_exam", return_value={
            "score": 100.0,
            "feedback": "Làm bài nghe rất xuất sắc.",
            "review_items": [{"id": qid, "explanation": "Đáp án đúng"} for qid in q_ids],
            "section_scores": {"listening": 100.0}
        }):
            submit_resp = self.client.post(
                f"/api/exams/{exam_id}/submit",
                headers=self.headers,
                json={"version": exam["version"], "answers": correct_answers},
            )
        self.assertEqual(submit_resp.status_code, 201)
        result = submit_resp.json()
        self.assertEqual(result["score"], 100.0)
        self.assertEqual(result["feedback"], "Làm bài nghe rất xuất sắc.")

        # Verify review items contain transcript and explanation
        snapshot = json.loads(result["content"])
        self.assertEqual(len(snapshot["questions"]), len(q_ids))
        for item in snapshot["questions"]:
            self.assertIn("transcript", item)
            self.assertIn("explanation", item)


if __name__ == "__main__":
    unittest.main()
