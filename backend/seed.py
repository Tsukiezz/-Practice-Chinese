"""Idempotent content examples. Does not create users or fabricated results."""
import json
from database import database, init_db

WORDS = [
    ("一", "yī", "một", 1, "一个人", [[{"x": 180, "y": 512}, {"x": 840, "y": 512}]]),
    ("你好", "nǐ hǎo", "xin chào", 1, "你好！很高兴认识你。", []),
    ("学习", "xué xí", "học tập", 1, "我学习汉语。", []),
    ("帮助", "bāng zhù", "giúp đỡ", 2, "谢谢你的帮助。", []),
    ("环境", "huán jìng", "môi trường", 3, "这里的环境很好。", []),
    ("经验", "jīng yàn", "kinh nghiệm", 4, "他有丰富的经验。", []),
    ("效率", "xiào lǜ", "hiệu suất", 5, "这个方法提高了效率。", []),
    ("毅力", "yì lì", "nghị lực", 6, "学习需要毅力。", []),
]


def seed():
    init_db()
    with database() as conn:
        for hanzi, pinyin, meaning, hsk, example, strokes in WORDS:
            conn.execute("INSERT OR IGNORE INTO vocabulary(hanzi,pinyin,meaning,hsk,example,strokes_json) VALUES(?,?,?,?,?,?)",
                         (hanzi, pinyin, meaning, hsk, example, json.dumps(strokes)))
        for level in range(1, 7):
            title = f"HSK {level} · Đọc hiểu mẫu"
            if conn.execute("SELECT 1 FROM exams WHERE title=?", (title,)).fetchone():
                continue
            word = conn.execute("SELECT * FROM vocabulary WHERE hsk=? ORDER BY id LIMIT 1", (level,)).fetchone()
            question = {"id": "q1", "section": "reading", "prompt": f"Chọn nghĩa của từ: {word['hanzi']}",
                        "options": [word["meaning"], "ngày mai", "màu xanh"], "answer": word["meaning"],
                        "audio_url": "", "transcript": "", "explanation": f"{word['hanzi']} ({word['pinyin']}): {word['meaning']}", "word_id": word["id"]}
            eid = conn.execute("INSERT INTO exams(title,hsk,status,duration_minutes,questions_json) VALUES(?,?,'draft',10,?)",
                               (title, level, json.dumps([question], ensure_ascii=False))).lastrowid
            conn.execute("INSERT OR IGNORE INTO exam_words VALUES(?,?)", (eid, word["id"]))

        listening_title = "HSK 1 · Nghe hiểu mẫu"
        if not conn.execute("SELECT 1 FROM exams WHERE title=?", (listening_title,)).fetchone():
            listening_word = conn.execute("SELECT * FROM vocabulary WHERE hsk=1 ORDER BY id LIMIT 1").fetchone()
            listening_question = {
                "id": "l1",
                "section": "listening",
                "prompt": "Nghe và chọn nghĩa đúng",
                "options": [listening_word["meaning"], "ngày mai", "màu xanh"],
                "answer": listening_word["meaning"],
                "audio_url": "https://traffic.libsyn.com/secure/learnchinese/H10901.mp3",
                "transcript": f"{listening_word['hanzi']} ({listening_word['pinyin']}): {listening_word['meaning']}",
                "explanation": listening_word["example"],
                "word_id": listening_word["id"],
            }
            conn.execute(
                "INSERT INTO exams(title,hsk,status,duration_minutes,questions_json) VALUES(?,?,'draft',10,?)",
                (listening_title, 1, json.dumps([listening_question], ensure_ascii=False)),
            )


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    seed()
    print("Đã thêm nội dung mẫu HSK 1–6. Đề ở trạng thái nháp để Admin kiểm tra trước khi phát hành.")
