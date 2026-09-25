"""UC-05 tests for per-character handwriting retry selection."""
import json
from pathlib import Path
import sys
import unittest
import uuid

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

import database as storage
from main import app
from services import build_handwriting_retry_items


def handwriting_row(row_id, target, score, created_at):
    return {
        "id": row_id,
        "kind": "handwriting",
        "content": json.dumps({"target": target}, ensure_ascii=False),
        "score": score,
        "created_at": created_at,
    }


class HandwritingRetryLogicTest(unittest.TestCase):
    def test_empty_history_has_no_retry_items(self):
        self.assertEqual(build_handwriting_retry_items([]), [])

    def test_latest_attempt_controls_completion_and_reentry(self):
        rows = [
            handwriting_row(1, "一", 35, 10),
            handwriting_row(2, "一", 80, 20),
            handwriting_row(3, "你", 55, 30),
        ]
        items = build_handwriting_retry_items(rows)
        self.assertEqual(items, [{
            "hanzi": "你", "latest_score": 55.0,
            "attempts": 1, "last_practiced_at": 30,
        }])

        rows.append(handwriting_row(4, "一", 70, 40))
        items = build_handwriting_retry_items(rows)
        self.assertEqual([item["hanzi"] for item in items], ["你", "一"])
        one = next(item for item in items if item["hanzi"] == "一")
        self.assertEqual((one["latest_score"], one["attempts"]), (70.0, 3))

    def test_exam_canvas_counts_as_an_attempt_and_sorts_lowest_first(self):
        exam_snapshot = {
            "questions": [
                {"id": "c1", "question_type": "hanzi_canvas", "answer": "人"},
                {"id": "e1", "question_type": "essay", "answer": "rubric"},
            ],
            "question_scores": {
                "c1": {"score": 25},
                "e1": {"score": 10},
            },
        }
        rows = [
            handwriting_row(1, "你", 60, 10),
            {"id": 2, "kind": "exam",
             "content": json.dumps(exam_snapshot, ensure_ascii=False),
             "score": 50, "created_at": 20},
        ]
        items = build_handwriting_retry_items(rows)
        self.assertEqual([item["hanzi"] for item in items], ["人", "你"])
        self.assertEqual(items[0]["attempts"], 1)


class HandwritingRetryEndpointTest(unittest.TestCase):
    def setUp(self):
        self.old_path = storage.DB_PATH
        self.test_path = Path(__file__).with_name(
            f".test-handwriting-retry-{uuid.uuid4().hex}.db")
        storage.DB_PATH = self.test_path
        self.client = TestClient(app)
        self.client.__enter__()
        self.admin = self._register("admin-retry@example.test", "Admin")
        self.student = self._register("student-retry@example.test", "Student")
        self.other = self._register("other-retry@example.test", "Other")
        with storage.database() as conn:
            conn.execute("UPDATE users SET role='admin' WHERE id=?",
                         (self.admin["user"]["id"],))
        self.admin_headers = {
            "Authorization": "Bearer " + self.admin["token"]}
        self.student_headers = {
            "Authorization": "Bearer " + self.student["token"]}
        self.other_headers = {
            "Authorization": "Bearer " + self.other["token"]}
        self.stroke = [
            [{"x": 100, "y": 500}, {"x": 900, "y": 500}],
        ]
        response = self.client.post(
            "/api/admin/vocabulary",
            headers=self.admin_headers,
            json={"hanzi": "一", "pinyin": "yī", "meaning": "một",
                  "hsk": 1, "strokes": self.stroke},
        )
        self.assertEqual(response.status_code, 201, response.text)

    def tearDown(self):
        self.client.__exit__(None, None, None)
        storage.DB_PATH = self.old_path
        self.test_path.unlink(missing_ok=True)

    def _register(self, email, name):
        response = self.client.post("/api/auth/register", json={
            "email": email, "name": name, "password": "Test-password-123"})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def _submit(self, strokes):
        response = self.client.post(
            "/api/handwriting/submit",
            headers=self.student_headers,
            json={"target": "一", "strokes": strokes},
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def _items(self):
        response = self.client.get(
            "/api/me/handwriting-retry-items",
            headers=self.student_headers,
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_pass_removes_character_and_later_failure_adds_it_again(self):
        reversed_stroke = [list(reversed(self.stroke[0]))]
        self.assertEqual(self._submit(reversed_stroke)["score"], 70)
        self.assertEqual(self._items()[0]["attempts"], 1)
        self.assertEqual(
            self.client.get("/api/me/handwriting-retry-items",
                            headers=self.other_headers).json(),
            [],
        )

        self.assertEqual(self._submit(self.stroke)["score"], 100)
        self.assertEqual(self._items(), [])

        self.assertEqual(self._submit(reversed_stroke)["score"], 70)
        item = self._items()[0]
        self.assertEqual(item["hanzi"], "一")
        self.assertEqual((item["latest_score"], item["attempts"]), (70, 3))


if __name__ == "__main__":
    unittest.main()
