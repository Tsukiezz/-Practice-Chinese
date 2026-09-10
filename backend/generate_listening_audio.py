"""Optional content authoring: pip install edge-tts; python generate_listening_audio.py."""
import asyncio
from pathlib import Path
import edge_tts
from listening_demo import LESSONS


async def generate():
    folder = Path(__file__).parent / 'media'
    folder.mkdir(exist_ok=True)
    for slug, _, transcript, *_ in LESSONS:
        target = folder / f'listening-{slug}.mp3'
        await edge_tts.Communicate(transcript, 'zh-CN-XiaoxiaoNeural', rate='-15%').save(str(target))
        print(target.name, target.stat().st_size, flush=True)


if __name__ == '__main__':
    asyncio.run(generate())
