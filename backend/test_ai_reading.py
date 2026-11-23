import json
import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from main import app, hash_password
from database import database
from ai_reading import (
    init_reading_tables,
    load_reading_topics,
    normalize_pinyin_to_tone_number,
    evaluate_pronunciation_offline,
)


class TestAiReading(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with database() as conn:
            init_reading_tables(conn)
        cls.client = TestClient(app)
        cls.email = "test_student_reading@example.test"
        cls.password = "ReadingPassword123@"
        with database() as conn:
            row = conn.execute("SELECT id FROM users WHERE email=?", (cls.email,)).fetchone()
            if not row:
                salt = "11" * 16
                pwd_hash = hash_password(cls.password, salt)
                conn.execute(
                    "INSERT INTO users(name, email, password_hash, salt, role, is_active, created_at) VALUES(?,?,?,?,?,?,?)",
                    ("Reading Tester", cls.email, pwd_hash, salt, "student", 1, 1000000),
                )
        res = cls.client.post("/api/auth/login", json={"email": cls.email, "password": cls.password})
        assert res.status_code == 200, res.text
        cls.student_auth = {"Authorization": f"Bearer {res.json()['token']}"}

    def test_reading_topics(self):
        """Verify list of 22 topics is returned."""
        res = self.client.get("/api/reading/topics")
        self.assertEqual(res.status_code, 200)
        topics = res.json()
        self.assertGreaterEqual(len(topics), 20)
        topic_ids = [t["id"] for t in topics]
        self.assertIn("family", topic_ids)
        self.assertIn("food", topic_ids)
        self.assertIn("home", topic_ids)
        self.assertIn("school", topic_ids)
        self.assertIn("work", topic_ids)
        self.assertIn("travel", topic_ids)

    def test_reading_vocabulary_hsk(self):
        """Verify vocabulary can be filtered by HSK 1 through HSK 6."""
        for hsk in (1, 2, 3, 4, 5, 6):
            res = self.client.get(f"/api/reading/vocabulary?hsk={hsk}&limit=10")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertGreater(data["total"], 0)
            self.assertGreater(len(data["items"]), 0)
            for item in data["items"]:
                self.assertEqual(item["hsk"], hsk)
                self.assertIn("hanzi", item)
                self.assertIn("pinyin", item)
                self.assertIn("meaning", item)

    def test_reading_vocabulary_topic(self):
        """Verify vocabulary can be filtered by topic."""
        res = self.client.get("/api/reading/vocabulary?topic=family&limit=10")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreater(data["total"], 0)
        self.assertGreater(len(data["items"]), 0)

    def test_pinyin_normalization(self):
        """Verify pinyin with diacritics is accurately converted to tone numbers."""
        self.assertEqual(normalize_pinyin_to_tone_number("nǐ hǎo"), "ni3 hao3")
        self.assertEqual(normalize_pinyin_to_tone_number("mā ma"), "ma1 ma5")
        self.assertEqual(normalize_pinyin_to_tone_number("xué xí"), "xue2 xi2")

    def test_offline_pronunciation_evaluator(self):
        """Text matching never produces an acoustic grade."""
        for spoken in ('你好', '', 'xue1 xi1'):
            result = evaluate_pronunciation_offline('你好', 'nǐ hǎo', spoken, has_audio=True)
            for key in ('accuracy_percent', 'tone_score', 'phoneme_score', 'fluency_score'):
                self.assertIsNone(result[key])
            self.assertFalse(result['score_eligible'])
            self.assertEqual(result['spoken_recognized'], spoken)
        exact = evaluate_pronunciation_offline('你好', 'nǐ hǎo', '你好')
        self.assertEqual(exact['transcript_match_percent'], 100.0)

    def test_reading_evaluate_endpoint(self):
        """Test full reading evaluation API with user authentication & history persistence."""
        payload = {
            "target_hanzi": "学习",
            "target_pinyin": "xuéxí",
            "target_meaning": "Học tập",
            "spoken_text": "学习",
            "save_history": True,
        }
        res = self.client.post("/api/reading/evaluate", json=payload, headers=self.student_auth)
        self.assertEqual(res.status_code, 200, res.text)
        data = res.json()
        self.assertEqual(data["target_hanzi"], "学习")
        self.assertIsNone(data["accuracy_percent"])
        self.assertEqual(data["assessment_status"], "transcript_only")
        self.assertIn("tone_score", data)
        self.assertIn("phoneme_score", data)
        self.assertIn("errors", data)
        self.assertIn("corrections", data)
        self.assertIsNone(data["history_id"])
        self.assertFalse(data["score_eligible"])

    def test_unauthenticated_reading_evaluate(self):
        """Verify guest learners can evaluate reading without requiring login."""
        payload = {
            "target_hanzi": "你好",
            "target_pinyin": "nǐ hǎo",
            "target_meaning": "Xin chào",
            "spoken_text": "你好",
            "save_history": False,
        }
        res = self.client.post("/api/reading/evaluate", json=payload)
        self.assertEqual(res.status_code, 200, res.text)
        data = res.json()
        self.assertEqual(data["target_hanzi"], "你好")
        self.assertIsNone(data["history_id"])
        self.assertIsNone(data["accuracy_percent"])
        self.assertEqual(data["transcript_match_percent"], 100.0)


if __name__ == "__main__":
    unittest.main()
