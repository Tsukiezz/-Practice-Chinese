"""Small end-to-end translation benchmark; uses real Gemini quota on cache misses.

python scripts/benchmark_ai_speed.py --output outputs/ai-speed/after.json
The three synthetic samples check negation, quantities and conditional meaning.
"""
import argparse
import json
from pathlib import Path
import statistics
import time

import httpx

SAMPLES = [
    {'text': '我今天不能参加下午三点的会议。', 'source': 'zh', 'target': 'vi'},
    {'text': 'Ngày mai tôi sẽ trả lại cho bạn ba quyển sách.', 'source': 'vi', 'target': 'zh'},
    {'text': '如果下雨，我们就不去公园。', 'source': 'zh', 'target': 'vi'},
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='https://hanzigo-chinese-learning.vercel.app')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--repeats', type=int, choices=(1, 2), default=2)
    args = parser.parse_args()
    report = {'url': args.url, 'cases': [], 'limits':
        'Three samples are a smoke benchmark, not a latency SLA or pedagogical evaluation. '
        'Cache is private and local to each warm server process; a new instance may miss.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=65, follow_redirects=True) as client:
        client.get(args.url.rstrip('/') + '/api/health').raise_for_status()
        for sample in SAMPLES:
            for repeat in range(args.repeats):
                start = time.perf_counter()
                response = client.post(args.url.rstrip('/') + '/api/translation/text', json=sample)
                try: data = response.json()
                except ValueError: data = {}
                case = {**sample, 'repeat': repeat, 'http': response.status_code,
                    'seconds': round(time.perf_counter() - start, 3),
                    'translation': data.get('translation'), 'error': data.get('detail'),
                    'cache': response.headers.get('X-HanziGo-AI-Cache'),
                    'attempts': response.headers.get('X-HanziGo-AI-Attempts'),
                    'server_timing': response.headers.get('Server-Timing')}
                report['cases'].append(case)
                args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
                print(json.dumps(case, ensure_ascii=False), flush=True)
    first = [c['seconds'] for c in report['cases'] if c['repeat'] == 0 and c['http'] == 200]
    hits = [c['seconds'] for c in report['cases'] if c['cache'] == 'hit' and c['http'] == 200]
    report['median_first_seconds'] = statistics.median(first) if first else None
    report['median_cache_hit_seconds'] = statistics.median(hits) if hits else None
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0 if all(c['http'] == 200 for c in report['cases']) else 1


if __name__ == '__main__':
    raise SystemExit(main())
