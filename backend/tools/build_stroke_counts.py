"""Usage: python backend/tools/build_stroke_counts.py Unihan.zip graphics.txt."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile

source = Path(sys.argv[1])
counts, alternatives = {}, {}
with zipfile.ZipFile(source) as archive:
    for name in archive.namelist():
        for line in archive.read(name).decode('utf-8').splitlines():
            if not line or line.startswith('#'):
                continue
            code, field, value = line.split('\t', 2)
            ch = chr(int(code[2:], 16))
            if field == 'kTotalStrokes':
                counts[ch] = int(value)
            elif field == 'kAlternateTotalStrokes':
                for variant in value.split():
                    if ':' in variant:
                        number, regions = variant.split(':')
                        if 'G' in regions:
                            alternatives[ch] = int(number)
counts.update(alternatives)
graphics = Path(sys.argv[2])
written_counts = {row['character']: len(row['strokes']) for row in
                  (json.loads(line) for line in graphics.read_text(encoding='utf-8').splitlines())}
counts.update(written_counts)
data = Path(__file__).resolve().parents[1] / 'data'
corpus = json.loads((data / 'hsk20_source.json').read_text(encoding='utf-8'))
missing = sorted({ch for word in corpus for ch in word['hanzi'] if ch not in counts})
if missing:
    raise SystemExit(f'Uncovered corpus characters: {missing}')
(data / 'stroke_counts.json').write_text(json.dumps({
    'source': 'https://www.unicode.org/Public/18.0.0/ucd/Unihan.zip',
    'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'graphics_source': 'https://github.com/skishore/makemeahanzi/blob/master/graphics.txt',
    'graphics_sha256': hashlib.sha256(graphics.read_bytes()).hexdigest(),
    'convention': 'Make Me a Hanzi PRC written strokes; Unihan mainland G fallback',
    'counts': counts}, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
print(f'Covered {len(corpus)} corpus entries; {len(counts)} characters')
