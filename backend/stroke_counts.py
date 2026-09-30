"""Offline PRC written stroke counts; Unihan mainland (G) fallback."""
import json
from functools import lru_cache
from pathlib import Path
import unicodedata


@lru_cache(maxsize=1)
def counts():
    return json.loads((Path(__file__).parent / 'data' / 'stroke_counts.json').read_text(encoding='utf-8'))['counts']


def stroke_metadata(hanzi):
    parts = [{'hanzi': ch, 'count': counts().get(ch)} for ch in hanzi
             if 'CJK' in unicodedata.name(ch, '') or ch == '〇'
             or 0x20000 <= ord(ch) <= 0x3347F]
    missing = [part['hanzi'] for part in parts if part['count'] is None]
    return {'stroke_count': sum(p['count'] for p in parts) if parts and not missing else None,
            'stroke_counts': parts, 'stroke_count_missing': missing}
