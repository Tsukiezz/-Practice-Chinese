"""Bundled Make Me a Hanzi medians; covers every character in the vocabulary.
See data/MAKEMEAHANZI-COPYING.txt and data/MAKEMEAHANZI-APL.txt.
"""
import json
from functools import lru_cache
from pathlib import Path

@lru_cache(maxsize=1)
def _catalog():
    return json.loads((Path(__file__).parent / "data" / "stroke_guides.json").read_text(encoding="utf-8"))

def bundled_strokes(character: str) -> list:
    return _catalog().get(character, [])
