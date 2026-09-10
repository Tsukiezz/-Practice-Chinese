"""Unit tests for UC-03 grammar validation, caching and usage accounting."""
from pathlib import Path
import unittest
import uuid
from unittest.mock import Mock, patch

from fastapi import HTTPException
from pydantic import ValidationError

import database as storage
from database import init_db
from models import GrammarAnalysisRequest
from services import analyze_grammar_with_ai


VALID_OUTPUT = {
    "score": 72,
    "feedback": "Câu hiểu được nhưng thứ tự trạng từ chưa tự nhiên.",
    "details": {
        "errors": [{
            "position": "trước động từ 学习",
            "original": "学习每天",
            "suggestion": "每天学习",
            "reason": "Trạng từ thời gian thường đứng trước động từ.",
        }],
        "corrected_sentence": "我每天学习中文。",
    },
}


class GrammarAnalysisTest(unittest.TestCase):
    def setUp(self):
        self.old_path = storage.DB_PATH
        self.test_path = Path(__file__).with_name(
            f".test-translation-{uuid.uuid4().hex}.db")
        storage.DB_PATH = self.test_path
        init_db()
        with storage.database() as conn:
            conn.execute(
                """INSERT INTO users(
                       id,name,email,password_hash,salt,role,is_active,created_at
                   ) VALUES(1,'Student','student@example.test','hash','salt',
                            'student',1,1)"""
            )
        self.settings = {
            "model": "test-model",
            "api_key": "not-a-real-key",
            "system_prompt": "Test",
            "temperature": 0.2,
            "max_tokens": 1000,
        }

    def tearDown(self):
        storage.DB_PATH = self.old_path
        self.test_path.unlink(missing_ok=True)

    def test_identical_input_uses_cache_and_logs_one_api_call(self):
        provider = Mock(return_value=VALID_OUTPUT)
        with patch("services.ai_settings", return_value=self.settings):
            first = analyze_grammar_with_ai(
                1, "我学习每天中文。", "Tôi học tiếng Trung mỗi ngày.", provider)
            second = analyze_grammar_with_ai(
                1, "我学习每天中文。", "Tôi học tiếng Trung mỗi ngày.", provider)

        self.assertEqual(first, second)
        self.assertEqual(first["details"]["corrected_sentence"],
                         "我每天学习中文。")
        provider.assert_called_once()
        with storage.database() as conn:
            usage = conn.execute(
                "SELECT module,status FROM ai_usage").fetchall()
            cache_count = conn.execute(
                "SELECT COUNT(*) FROM grammar_cache").fetchone()[0]
        self.assertEqual([tuple(row) for row in usage],
                         [("grammar_analysis", "success")])
        self.assertEqual(cache_count, 1)

    def test_malformed_provider_response_is_rejected_and_logged(self):
        provider = Mock(return_value={
            "score": 101,
            "feedback": "invalid",
            "details": {"errors": [], "corrected_sentence": ""},
        })
        with patch("services.ai_settings", return_value=self.settings):
            with self.assertRaises(HTTPException) as raised:
                analyze_grammar_with_ai(1, "我很好。", "", provider)

        self.assertEqual(raised.exception.status_code, 502)
        with storage.database() as conn:
            usage = conn.execute(
                "SELECT module,status FROM ai_usage").fetchone()
        self.assertEqual(tuple(usage), ("grammar_analysis", "error"))

    def test_request_limits_length_and_requires_han_character(self):
        with self.assertRaises(ValidationError):
            GrammarAnalysisRequest(sentence="a" * 201)
        with self.assertRaises(ValidationError):
            GrammarAnalysisRequest(sentence="Toi hoc tieng Trung")


if __name__ == "__main__":
    unittest.main()
