import json
from pathlib import Path
import unittest
from unittest.mock import patch
from stroke_counts import stroke_metadata
from services import compare_handwriting_strokes


class StrokeRegressionTest(unittest.TestCase):
    def test_entire_corpus_has_complete_counts(self):
        corpus = json.loads((Path(__file__).parent / 'data/hsk20_source.json').read_text(encoding='utf-8'))
        self.assertEqual(len(corpus), 5000)
        for word in corpus:
            meta = stroke_metadata(word['hanzi'])
            self.assertFalse(meta['stroke_count_missing'], word['hanzi'])
            self.assertGreater(meta['stroke_count'], 0, word['hanzi'])

    def test_known_simplified_counts_and_repeated_characters(self):
        for word, expected in [('车', 4), ('脑', 10), ('帮', 9), ('你好', 13), ('谢谢', 24)]:
            self.assertEqual(stroke_metadata(word)['stroke_count'], expected)

    def test_unknown_character_never_produces_partial_total(self):
        with patch('stroke_counts.counts', return_value={'你': 7}):
            self.assertIsNone(stroke_metadata('你好')['stroke_count'])

    def test_translation_and_scale_do_not_reduce_grade(self):
        original = [[{'x': 100, 'y': 100}, {'x': 800, 'y': 100}],
                    [{'x': 450, 'y': 100}, {'x': 450, 'y': 800}]]
        shifted = [[{'x': p['x'] * .6 + 200, 'y': p['y'] * .6 + 100} for p in stroke] for stroke in original]
        self.assertEqual(compare_handwriting_strokes(original, shifted)['score'], 100)
        shifted[0][1]['y'] += 70
        self.assertGreater(compare_handwriting_strokes(original, shifted)['score'], 80)

    def test_small_attempt_receives_low_positive_score(self):
        stroke = [{'x': 0, 'y': 0}, {'x': 100, 'y': 0}]
        score = compare_handwriting_strokes([stroke] * 40, [list(reversed(stroke))])['score']
        self.assertGreaterEqual(score, 5)
        self.assertLess(score, 30)
        with self.assertRaises(ValueError):
            compare_handwriting_strokes([stroke], [])
