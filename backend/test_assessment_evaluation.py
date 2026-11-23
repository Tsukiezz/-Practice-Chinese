import unittest
from tools.evaluate_assessments import evaluate


class AssessmentEvaluationTests(unittest.TestCase):
    def row(self, identifier, **values):
        return {'id': identifier, 'kind': 'handwriting', 'split': 'test', 'label_source': 'teacher',
                'reviewer': 'test-fixture-reviewer', 'prediction_source': 'offline-vector-v2',
                'assessment_status': 'assessed', 'reference_score': 80, 'predicted_score': 70, **values}

    def test_missing_labels_do_not_report_accuracy(self):
        result = evaluate([self.row('a', reference_score=None, reviewer=None)])
        self.assertEqual(result['evidence_status'], 'awaiting_teacher_labels')
        self.assertIsNone(result['metrics']['handwriting'])

    def test_score_errors_use_independent_references(self):
        result = evaluate([self.row('a'), self.row('b', reference_score=90, predicted_score=94)])
        self.assertEqual(result['metrics']['handwriting']['mae'], 7)
        self.assertEqual(result['metrics']['handwriting']['mean_signed_error'], -3)

    def test_fallback_and_calibration_cases_are_excluded(self):
        result = evaluate([self.row('a', prediction_source='stroke-count-fallback'), self.row('b', split='calibration')])
        self.assertEqual(result['included_cases'], 0)
        self.assertEqual(sum(result['excluded'].values()), 2)

    def test_invalid_scores_and_duplicate_ids_are_rejected(self):
        with self.assertRaises(ValueError): evaluate([self.row('a', predicted_score=float('nan'))])
        with self.assertRaises(ValueError): evaluate([self.row('a'), self.row('a')])

    def test_ocr_reports_top1_and_top3_separately(self):
        result = evaluate([self.row('a', kind='ocr', prediction_source='gemini_vision',
                                    reference_hanzi='你', predictions=['他', '你'])])
        self.assertEqual(result['metrics']['ocr']['top1_accuracy'], 0)
        self.assertEqual(result['metrics']['ocr']['top3_accuracy'], 1)
