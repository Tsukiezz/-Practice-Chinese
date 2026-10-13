"""Usage: python backend/tools/build_stroke_guides.py graphics.txt
Builds bundled guides for every character in the HSK corpus (Make Me a Hanzi).
Coordinates match the canvas: x unchanged, y = 900 - source y.
Licenses: backend/data/MAKEMEAHANZI-COPYING.txt, MAKEMEAHANZI-APL.txt.
"""
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1] / "data"
corpus = json.loads((root / "hsk20_source.json").read_text(encoding="utf-8"))
characters = set("".join(word["hanzi"] for word in corpus))
guides = {}
with Path(sys.argv[1]).open(encoding="utf-8") as source:
    for line in source:
        row = json.loads(line)
        if row["character"] in characters:
            guides[row["character"]] = [[{"x": round(x), "y": round(900-y)} for x,y in stroke] for stroke in row["medians"]]
missing = characters - guides.keys()
if missing:
    raise SystemExit(f"Missing stroke data: {sorted(missing)!r}")
(root / "stroke_guides.json").write_text(json.dumps(guides, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print(f"Bundled {len(guides)} characters for all {len(corpus)} corpus entries")
