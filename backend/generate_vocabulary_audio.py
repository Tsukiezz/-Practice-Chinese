"""Optional authoring: pip install edge-tts; python generate_vocabulary_audio.py.

Produces synthetic Mandarin pronunciation for the curated seed vocabulary.
No learner data or API keys are sent. Runtime playback uses bundled MP3 files.
"""
import asyncio
from pathlib import Path
import sys

_backend_dir = Path(__file__).resolve().parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

import edge_tts  # type: ignore
try:
    from seed import WORDS
except ImportError:
    from backend.seed import WORDS  # type: ignore



async def generate():
    folder = Path(__file__).parent / 'media'
    folder.mkdir(exist_ok=True)
    for hanzi, *_ in WORDS:
        slug = '-'.join(f'{ord(c):x}' for c in hanzi)
        target = folder / f'word-{slug}.mp3'
        if not target.exists():
            await edge_tts.Communicate(hanzi, 'zh-CN-XiaoxiaoNeural', rate='-15%').save(str(target))
        print(target.name, target.stat().st_size, flush=True)


if __name__ == '__main__':
    asyncio.run(generate())
