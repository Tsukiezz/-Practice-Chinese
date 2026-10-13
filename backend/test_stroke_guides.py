import json
from pathlib import Path
import unittest
from stroke_guides import bundled_strokes
from stroke_counts import stroke_metadata

class BundledGuidesTest(unittest.TestCase):
    def test_entire_hsk_corpus_has_real_ordered_strokes(self):
        corpus = json.loads((Path(__file__).parent / "data/hsk20_source.json").read_text(encoding="utf-8"))
        characters = set("".join(word["hanzi"] for word in corpus))
        self.assertEqual(len(characters), 2632)
        for char in characters:
            strokes = bundled_strokes(char)
            self.assertEqual(len(strokes), stroke_metadata(char)["stroke_count"], char)
            for stroke in strokes:
                self.assertGreaterEqual(len(stroke), 2, char)
                for point in stroke:
                    self.assertGreaterEqual(point["x"], 0, char)
                    self.assertLessEqual(point["x"], 1024, char)
                    self.assertGreaterEqual(point["y"], 0, char)
                    self.assertLessEqual(point["y"], 1024, char)
    def test_unknown_character_has_no_fabricated_guide(self):
        self.assertEqual(bundled_strokes("?"), [])
