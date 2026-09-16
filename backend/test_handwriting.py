"""Unit tests for deterministic, offline handwriting grading."""
import json
from pathlib import Path
import unittest
import uuid

import database as storage
from seed import seed
from services import compare_handwriting_strokes


class HandwritingAlgorithmTest(unittest.TestCase):
    def setUp(self):
        self.horizontal = [{"x": 100, "y": 300}, {"x": 900, "y": 300}]
        self.vertical = [{"x": 500, "y": 150}, {"x": 500, "y": 850}]

    def test_identical_strokes_receive_full_score(self):
        grade = compare_handwriting_strokes(
            [self.horizontal, self.vertical],
            [self.horizontal, self.vertical],
        )

        self.assertEqual(grade["score"], 100)
        self.assertEqual(grade["details"]["wrong_strokes"], [])
        self.assertEqual(grade["details"]["count_score"], 100)
        self.assertEqual(grade["details"]["order_position_score"], 100)
        self.assertEqual(grade["details"]["direction_score"], 100)

    def test_reversed_direction_loses_direction_component(self):
        reversed_horizontal = list(reversed(self.horizontal))
        grade = compare_handwriting_strokes(
            [self.horizontal],
            [reversed_horizontal],
        )

        self.assertEqual(grade["score"], 70)
        self.assertEqual(grade["details"]["wrong_strokes"], [1])
        self.assertEqual(grade["details"]["direction_score"], 0)

    def test_swapped_strokes_are_reported_in_one_based_order(self):
        grade = compare_handwriting_strokes(
            [self.horizontal, self.vertical],
            [self.vertical, self.horizontal],
        )

        self.assertEqual(grade["score"], 30)
        self.assertEqual(grade["details"]["wrong_strokes"], [1, 2])

    def test_missing_stroke_reduces_count_and_ordered_identity_scores(self):
        grade = compare_handwriting_strokes(
            [self.horizontal, self.vertical],
            [self.horizontal],
        )

        self.assertEqual(grade["score"], 30)
        self.assertEqual(grade["details"]["wrong_strokes"], [1, 2])


class HandwritingSeedTest(unittest.TestCase):
    def test_seed_contains_demo_strokes_for_26_single_characters(self):
        old_path = storage.DB_PATH
        test_path = Path(__file__).with_name(
            f".test-handwriting-{uuid.uuid4().hex}.db")
        try:
            storage.DB_PATH = test_path
            seed()
            with storage.database() as conn:
                rows = conn.execute(
                    "SELECT hanzi,strokes_json FROM vocabulary"
                ).fetchall()
            samples = [row for row in rows
                       if len(row["hanzi"]) == 1
                       and json.loads(row["strokes_json"])]
            self.assertEqual(len(samples), 26)
        finally:
            storage.DB_PATH = old_path
            test_path.unlink(missing_ok=True)

if __name__ == "__main__":
    unittest.main()
