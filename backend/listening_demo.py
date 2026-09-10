"""Reproducible listening content with bundled Mandarin speech, no learner results."""
import json
from pathlib import Path
from database import database, init_db

LESSONS = [
    ("greeting", "Chào hỏi", "你好！我叫小明。我是中国人。", "Người nói tên là gì?",
     ["Tiểu Minh", "Tiểu Lan", "Đại Vệ"], "Tiểu Minh", "我叫小明 nghĩa là Tôi tên Tiểu Minh."),
    ("time", "Thời gian", "现在是上午八点。我九点去学校。", "Người nói đi học lúc mấy giờ?",
     ["7 giờ", "8 giờ", "9 giờ"], "9 giờ", "九点去学校: đi đến trường lúc 9 giờ; 8 giờ là thời gian hiện tại."),
    ("shopping", "Mua sắm", "这个苹果三块钱。我要买两个苹果。", "Người nói muốn mua bao nhiêu quả táo?",
     ["Hai quả", "Ba quả", "Một quả"], "Hai quả", "两个苹果 là hai quả táo; 三块钱 là giá một quả."),
]


def seed_listening(publish=False):
    init_db()
    with database() as conn:
        for slug, topic, transcript, prompt, options, answer, explanation in LESSONS:
            media = Path(__file__).parent / 'media' / f'listening-{slug}.mp3'
            if not media.is_file() or media.stat().st_size < 1000:
                raise RuntimeError(f'Missing listening audio: {media.name}')
            title = f'HSK 1 · Nghe {topic} (mẫu)'
            if conn.execute('SELECT id FROM exams WHERE title=?', (title,)).fetchone():
                continue  # Never overwrite Admin edits or republish a hidden exam.
            questions = [{
                'id': slug, 'section': 'listening', 'prompt': prompt,
                'options': options, 'answer': answer,
                'audio_url': f'/media/listening-{slug}.mp3',
                'transcript': transcript, 'explanation': explanation, 'word_id': None,
            }]
            conn.execute('INSERT INTO exams(title,hsk,status,duration_minutes,questions_json) VALUES(?,1,?,5,?)',
                         (title, 'published' if publish else 'draft', json.dumps(questions, ensure_ascii=False)))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--publish', action='store_true', help='Publish only newly inserted demo lessons')
    seed_listening(parser.parse_args().publish)
    print('Listening demo ready: 3 lessons; existing data preserved.')
