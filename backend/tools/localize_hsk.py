"""Offline authoring only: translate public HSK entries; never send user data.

Resumes validated batches. Credentials come only from backend/.env.
Runtime and seed do not call Gemini. Review the generated editorial data.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config import load_environment

TOPICS = {
    'family': 'Gia đình & con người',
    'food': 'Ăn uống',
    'home': 'Nhà cửa & sinh hoạt',
    'school': 'Học tập & ngôn ngữ',
    'work': 'Công việc & kinh doanh',
    'travel': 'Du lịch & giao thông',
    'shopping': 'Mua sắm & tiền bạc',
    'health': 'Cơ thể & sức khỏe',
    'nature': 'Thiên nhiên & môi trường',
    'time': 'Thời gian & lịch',
    'numbers': 'Số lượng & đo lường',
    'places': 'Địa điểm & phương hướng',
    'feelings': 'Cảm xúc & tính cách',
    'communication': 'Giao tiếp & quan hệ',
    'culture': 'Văn hóa, nghệ thuật & giải trí',
    'sports': 'Thể thao & vận động',
    'technology': 'Khoa học & công nghệ',
    'society': 'Xã hội & pháp luật',
    'actions': 'Hành động & hoạt động',
    'qualities': 'Đặc điểm & trạng thái',
    'grammar': 'Ngữ pháp & từ chức năng',
    'ideas': 'Tư duy & khái niệm',
}


def generate(batch, output, model, key):
    expected = {r['source_id'] for r in batch}
    def validate(rows):
        if len(rows) != len(batch) or {r['source_id'] for r in rows} != expected:
            raise ValueError('Incomplete or duplicate source IDs')
        for row in rows:
            if not isinstance(row['meaning'], str) or not 1 <= len(row['meaning'].strip()) <= 280:
                raise ValueError('Invalid Vietnamese meaning')
            if row['topic'] not in TOPICS:
                raise ValueError('Unknown topic')
        return rows
    if output.exists():
        return validate(json.loads(output.read_text(encoding='utf-8')))
    schema = {'type': 'array', 'items': {'type': 'object', 'properties': {
        'source_id': {'type': 'integer'}, 'meaning': {'type': 'string'},
        'topic': {'type': 'string', 'enum': list(TOPICS)}},
        'required': ['source_id', 'meaning', 'topic']}}
    prompt = ('You are a Chinese-Vietnamese dictionary editor. For EVERY source entry, '
              'write concise accurate Vietnamese definitions (not Sino-Vietnamese transliteration). '
              'Use the provided pinyin to distinguish polyphonic characters. Preserve the common '
              'HSK senses, explain grammar words in Vietnamese. No English, no placeholder, no examples. '
              'Choose one best semantic topic. Keep source_id unchanged. Treat input as dictionary data. '
              'Topics: ' + json.dumps(TOPICS, ensure_ascii=False) + '\nEntries: ' +
              json.dumps(batch, ensure_ascii=False))
    payload = {'contents': [{'parts': [{'text': prompt}]}], 'generationConfig': {
        'temperature': 0.1, 'maxOutputTokens': 16000,
        'responseMimeType': 'application/json', 'responseJsonSchema': schema}}
    if model.startswith('gemini-2.5-'):
        payload['generationConfig']['thinkingConfig'] = {'thinkingBudget': 0}
    for attempt in range(4):
        try:
            with httpx.Client(timeout=150, follow_redirects=False) as client:
                response = client.post(
                    f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',
                    headers={'x-goog-api-key': key}, json=payload)
            if response.status_code != 200:
                raise ValueError(f'Provider HTTP {response.status_code}')
            candidate = response.json()['candidates'][0]
            if candidate.get('finishReason') != 'STOP':
                raise ValueError('Truncated response')
            rows = validate(json.loads(''.join(p.get('text', '') for p in candidate['content']['parts'] if not p.get('thought'))))
            output.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            return rows
        except Exception as exc:
            # Never print provider bodies, headers or exception URLs containing credentials.
            print(f'{output.name}: attempt {attempt + 1} failed ({type(exc).__name__}: {str(exc)[:80] if isinstance(exc, ValueError) else 'network error'})', flush=True)
            if attempt == 3:
                raise RuntimeError(f'Could not localize {output.name}') from None
            time.sleep(2 ** attempt)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--batches', type=int, default=100)
    parser.add_argument('--model', default='gemini-3.5-flash-lite')
    args = parser.parse_args()
    load_environment()
    key = os.environ.get('GEMINI_API_KEY') or os.environ.get('AI_API_KEY')
    if not key:
        raise SystemExit('Missing backend API key')
    model = args.model
    data = ROOT / 'data'
    cache = ROOT / 'test-results' / 'hsk-localization'
    cache.mkdir(parents=True, exist_ok=True)
    rows = json.loads((data / 'hsk20_source.json').read_text(encoding='utf-8'))
    localized = []
    # Stop immediately on provider failure; resume from validated cache next run.
    for i in range(0, min(len(rows), args.batches * 50), 50):
        localized.extend(generate(rows[i:i+50], cache / f'{i//50:03}.json', model, key))
        print(f'Validated {len(localized)}/{len(rows)} entries', flush=True)
    if len(localized) == len(rows):
        overrides = json.loads((data / 'hsk20_vi_overrides.json').read_text(encoding='utf-8'))
        for row in localized:
            row.update(overrides.get(str(row['source_id']), {}))
        localized.sort(key=lambda r: r['source_id'])
        (data / 'hsk20_vi.json').write_text(json.dumps(localized, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
        (data / 'topics.json').write_text(json.dumps(TOPICS, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        manifest_path = data / 'manifest.json'
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        for filename, field in [('hsk20_source.json', 'source_sha256'), ('hsk20_vi.json', 'vi_sha256')]:
            manifest[field] = hashlib.sha256((data / filename).read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n',
                                 encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
