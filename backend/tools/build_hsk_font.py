"""Optional asset authoring: python build_hsk_font.py path/to/NotoSansSC[wght].ttf.

Requires fonttools only on the authoring machine, not in the application.
Subset a local OFL font, keeping all characters in the bundled corpus and source UI.
"""
from pathlib import Path
import sys

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parents[2]
font = TTFont(sys.argv[1])
font = instantiateVariableFont(font, {'wght': 400}, inplace=True)
text = ''.join(p.read_text(encoding='utf-8') for folder, pattern in [
    ('backend/data', '*.json'), ('lib', '*.dart'), ('backend', '*.py')
] for p in (ROOT / folder).rglob(pattern))
unicodes = set(map(ord, text)) | set(range(32, 0x250)) | set(range(0x1E00, 0x1F00)) | set(range(0x3000, 0x3040))
missing_hanzi = [c for c in unicodes if 0x4E00 <= c <= 0x9FFF and c not in font.getBestCmap()]
if missing_hanzi:
    raise SystemExit('Source font is missing Chinese characters')
options = subset.Options()
options.name_IDs = ['*']
options.name_legacy = True
options.name_languages = ['*']
subsetter = subset.Subsetter(options=options)
subsetter.populate(unicodes=unicodes)
subsetter.subset(font)
for record in font['name'].names:
    names = {1: 'HanziGo HSK', 2: 'Regular', 3: 'HanziGoHSK-Regular',
             4: 'HanziGo HSK Regular', 6: 'HanziGoHSK-Regular', 16: 'HanziGo HSK', 17: 'Regular'}
    if record.nameID in names:
        record.string = names[record.nameID].encode(record.getEncoding())
output = ROOT / 'assets/fonts/HanziGoHSK-Regular.ttf'
output.parent.mkdir(parents=True, exist_ok=True)
font.save(output)
print(f'Bundled {len(font.getBestCmap())} characters, {output.stat().st_size} bytes')
