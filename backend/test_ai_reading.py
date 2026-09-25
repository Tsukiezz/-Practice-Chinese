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
        """Verify rule-based pronunciation evaluation and error detection."""
        # 1. Exact match
        res_exact = evaluate_pronunciation_offline("你好", "nǐ hǎo", "你好")
        self.assertEqual(res_exact["accuracy_percent"], 100.0)
        self.assertEqual(res_exact["rating"], "Xuất sắc")
        self.assertEqual(len(res_exact["errors"]), 0)

        # 2. Empty speech
        res_empty = evaluate_pronunciation_offline("你好", "nǐ hǎo", "")
        self.assertEqual(res_empty["accuracy_percent"], 0.0)
        self.assertEqual(res_empty["rating"], "Chưa đạt")
        self.assertGreater(len(res_empty["errors"]), 0)

        # 3. Recorded audio without WebSpeech transcript (e.g. mobile Safari)
        res_audio = evaluate_pronunciation_offline("你好", "nǐ hǎo", "", has_audio=True)
        self.assertGreaterEqual(res_audio["accuracy_percent"], 80.0)
        self.assertEqual(res_audio["rating"], "Tốt")
        self.assertEqual(res_audio["spoken_recognized"], "你好")

        # 4. Partial or different pronunciation
        res_diff = evaluate_pronunciation_offline("学习", "xuéxí", "xue1 xi1")
        self.assertTrue(10.0 <= res_diff["accuracy_percent"] <= 95.0)
        self.assertGreater(len(res_diff["corrections"]), 0)

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
        self.assertTrue(0.0 <= data["accuracy_percent"] <= 100.0)
        self.assertIn(data["rating"], ("Xuất sắc", "Tốt", "Cần cải thiện", "Chưa đạt", "Đạt"))
        self.assertIn("tone_score", data)
        self.assertIn("phoneme_score", data)
        self.assertIn("errors", data)
        self.assertIn("corrections", data)
        self.assertIsNotNone(data["history_id"])

        # Check that item appears in reading history
        history_res = self.client.get("/api/me/reading/history", headers=self.student_auth)
        self.assertEqual(history_res.status_code, 200)
        history_data = history_res.json()
        self.assertGreaterEqual(history_data["total"], 1)
        found = any(item["id"] == data["history_id"] for item in history_data["items"])
        self.assertTrue(found)

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
        self.assertGreaterEqual(data["accuracy_percent"], 90.0)


if __name__ == "__main__":
    unittest.main()
