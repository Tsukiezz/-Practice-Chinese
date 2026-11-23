"""Compare recorded predictions with independent teacher labels; no provider calls.

python backend/tools/evaluate_assessments.py --dataset cases.jsonl --output report.json
Unlabelled cases and fallback/unavailable predictions never become accuracy data.
"""
import argparse
from collections import Counter
import json
import math
from pathlib import Path


SOURCES = {'handwriting': 'offline-vector-v2', 'pronunciation': 'gemini_audio', 'ocr': 'gemini_vision'}


def score(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and 0 <= value <= 100


def evaluate(records):
    seen = set()
    pending = 0
    excluded = Counter()
    errors = {'handwriting': [], 'pronunciation': []}
    ocr = []
    for item in records:
        case_id = item.get('id')
        if not isinstance(case_id, str) or not case_id or case_id in seen:
            raise ValueError('Each case must have a unique nonempty id')
        seen.add(case_id)
        kind = item.get('kind')
        if kind not in SOURCES:
            raise ValueError('Unknown assessment kind: ' + str(kind))
        if item.get('split') != 'test':
            excluded['not_independent_test_split'] += 1
            continue
        reference = item.get('reference_hanzi') if kind == 'ocr' else item.get('reference_score')
        if reference is None or not item.get('reviewer'):
            pending += 1
            continue
        if item.get('label_source') != 'teacher':
            excluded['labels_not_from_teacher'] += 1
            continue
        if item.get('prediction_source') != SOURCES[kind] or item.get('assessment_status') != 'assessed':
            excluded['fallback_or_unavailable_prediction'] += 1
            continue
        if kind == 'ocr':
            candidates = item.get('predictions')
            if not isinstance(reference, str) or not reference.strip():
                raise ValueError('Invalid OCR reference: ' + case_id)
            if not isinstance(candidates, list) or not all(isinstance(v, str) for v in candidates):
                raise ValueError('Invalid OCR candidates: ' + case_id)
            ocr.append((reference, candidates))
        else:
            predicted = item.get('predicted_score')
            if not score(reference) or not score(predicted):
                raise ValueError('Scores must be finite numbers from 0 to 100: ' + case_id)
            errors[kind].append(predicted - reference)
    metrics = {}
    for kind, diffs in errors.items():
        metrics[kind] = None if not diffs else {
            'cases': len(diffs), 'mae': round(sum(abs(d) for d in diffs) / len(diffs), 4),
            'rmse': round(math.sqrt(sum(d*d for d in diffs) / len(diffs)), 4),
            'mean_signed_error': round(sum(diffs) / len(diffs), 4),
        }
    metrics['ocr'] = None if not ocr else {
        'cases': len(ocr),
        'top1_accuracy': sum(bool(pred) and ref == pred[0] for ref, pred in ocr) / len(ocr),
        'top3_accuracy': sum(ref in pred[:3] for ref, pred in ocr) / len(ocr),
    }
    included = sum(len(v) for v in errors.values()) + len(ocr)
    return {
        'evidence_status': 'computed_against_supplied_labels' if included else 'awaiting_teacher_labels',
        'total_cases': len(seen), 'included_cases': included, 'pending_teacher_labels': pending,
        'excluded': dict(excluded), 'metrics': metrics,
        'limitations': 'The tool cannot verify reviewer identity, dataset independence or pedagogical validity. '
                       'Report sample sizes and collection methods. Empty metrics are not zero accuracy.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    records = [json.loads(line) for line in args.dataset.read_text(encoding='utf-8-sig').splitlines() if line.strip()]
    report = evaluate(records)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + '\n', encoding='utf-8')
    print(rendered)


if __name__ == '__main__':
    main()
