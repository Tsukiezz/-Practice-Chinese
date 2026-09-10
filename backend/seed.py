"""Idempotent content examples. Does not create users or fabricated results."""
import json
from database import database, init_db


def stroke(*points):
    """Build a compact 0–1024 polyline for curated demo stroke data."""
    return [{"x": x, "y": y} for x, y in points]


WORDS = [
    ("一", "yī", "một", 1, "一个人", [[{"x": 180, "y": 512}, {"x": 840, "y": 512}]]),
    ("二", "èr", "hai", 1, "二个人", [
        stroke((300, 350), (720, 350)), stroke((180, 700), (850, 700))]),
    ("三", "sān", "ba", 1, "三个人", [
        stroke((330, 280), (690, 280)), stroke((270, 500), (750, 500)),
        stroke((170, 740), (850, 740))]),
    ("人", "rén", "người", 1, "一个人", [
        stroke((530, 190), (470, 470), (250, 820)),
        stroke((520, 350), (650, 590), (820, 820))]),
    ("大", "dà", "lớn", 1, "很大", [
        stroke((210, 430), (820, 430)),
        stroke((520, 180), (500, 500), (220, 840)),
        stroke((510, 480), (650, 670), (840, 840))]),
    ("小", "xiǎo", "nhỏ", 1, "很小", [
        stroke((520, 190), (520, 720), (470, 790)),
        stroke((330, 430), (210, 660)), stroke((700, 410), (830, 670))]),
    ("口", "kǒu", "miệng", 1, "人口", [
        stroke((260, 240), (260, 790)),
        stroke((260, 250), (780, 250), (780, 790)),
        stroke((260, 790), (780, 790))]),
    ("日", "rì", "ngày, mặt trời", 1, "今日", [
        stroke((280, 170), (280, 850)),
        stroke((280, 180), (760, 180), (760, 850)),
        stroke((290, 500), (750, 500)), stroke((280, 850), (760, 850))]),
    ("月", "yuè", "tháng, mặt trăng", 1, "一月", [
        stroke((300, 170), (300, 650), (230, 860)),
        stroke((300, 180), (740, 180), (740, 820), (690, 860)),
        stroke((310, 420), (730, 420)), stroke((310, 640), (730, 640))]),
    ("山", "shān", "núi", 1, "山上", [
        stroke((510, 160), (510, 800)),
        stroke((250, 390), (250, 810), (790, 810)),
        stroke((790, 370), (790, 810))]),
    ("水", "shuǐ", "nước", 1, "喝水", [
        stroke((510, 150), (510, 790), (450, 840)),
        stroke((220, 400), (430, 390), (250, 700)),
        stroke((780, 300), (600, 500), (470, 610)),
        stroke((590, 500), (700, 680), (850, 800))]),
    ("火", "huǒ", "lửa", 1, "火很大", [
        stroke((330, 300), (240, 520)), stroke((700, 280), (650, 490)),
        stroke((520, 160), (500, 520), (250, 840)),
        stroke((520, 540), (670, 720), (830, 840))]),
    ("木", "mù", "gỗ, cây", 1, "木头", [
        stroke((190, 420), (840, 420)), stroke((520, 150), (520, 850)),
        stroke((500, 450), (350, 650), (190, 800)),
        stroke((540, 450), (690, 650), (850, 790))]),
    ("本", "běn", "quyển, gốc", 1, "一本书", [
        stroke((190, 380), (840, 380)), stroke((520, 140), (520, 850)),
        stroke((500, 410), (340, 620), (180, 780)),
        stroke((540, 420), (700, 620), (860, 770)),
        stroke((330, 690), (710, 690))]),
    ("中", "zhōng", "giữa, Trung Quốc", 1, "中国", [
        stroke((260, 280), (260, 700)),
        stroke((260, 290), (780, 290), (780, 700)),
        stroke((260, 700), (780, 700)), stroke((520, 130), (520, 880))]),
    ("上", "shàng", "trên, lên", 1, "山上", [
        stroke((450, 180), (450, 760)), stroke((450, 450), (720, 450)),
        stroke((180, 780), (850, 780))]),
    ("下", "xià", "dưới, xuống", 1, "下午", [
        stroke((180, 260), (850, 260)), stroke((500, 270), (500, 820)),
        stroke((520, 480), (700, 610))]),
    ("个", "gè", "cái; lượng từ", 1, "一个人", [
        stroke((510, 170), (250, 590)), stroke((510, 170), (800, 580)),
        stroke((510, 390), (510, 850))]),
    ("天", "tiān", "trời, ngày", 1, "今天", [
        stroke((300, 240), (720, 240)), stroke((190, 450), (830, 450)),
        stroke((520, 260), (490, 560), (220, 830)),
        stroke((510, 540), (660, 700), (850, 830))]),
    ("不", "bù", "không", 1, "不是", [
        stroke((190, 250), (850, 250)), stroke((500, 270), (260, 700)),
        stroke((540, 310), (540, 850)), stroke((550, 470), (810, 710))]),
    ("你", "nǐ", "bạn", 1, "你好", [
        stroke((270, 170), (170, 430)), stroke((260, 350), (260, 850)),
        stroke((520, 170), (420, 350)),
        stroke((480, 330), (790, 330), (720, 450)),
        stroke((610, 380), (610, 820), (550, 860)),
        stroke((500, 540), (410, 730)), stroke((720, 530), (830, 740))]),
    ("他", "tā", "anh ấy", 1, "他很好", [
        stroke((250, 170), (150, 430)), stroke((240, 350), (240, 850)),
        stroke((390, 430), (820, 310), (780, 610)),
        stroke((540, 180), (540, 760)),
        stroke((390, 400), (390, 780), (760, 820), (830, 730))]),
    ("好", "hǎo", "tốt", 1, "你好", [
        stroke((290, 210), (210, 580), (430, 760)),
        stroke((410, 350), (310, 650), (150, 810)),
        stroke((170, 520), (450, 520)),
        stroke((570, 270), (820, 270), (700, 440)),
        stroke((690, 420), (690, 800), (630, 850)),
        stroke((500, 570), (850, 570))]),
    ("生", "shēng", "sinh, sống", 1, "学生", [
        stroke((360, 170), (250, 370)), stroke((300, 350), (740, 350)),
        stroke((240, 560), (790, 560)), stroke((520, 220), (520, 830)),
        stroke((170, 820), (850, 820))]),
    ("年", "nián", "năm", 1, "今年", [
        stroke((350, 150), (230, 340)), stroke((310, 300), (790, 300)),
        stroke((260, 480), (760, 480)), stroke((430, 310), (430, 700)),
        stroke((200, 690), (820, 690)), stroke((590, 300), (590, 880))]),
    ("有", "yǒu", "có", 1, "我有一本书", [
        stroke((250, 260), (830, 260)), stroke((500, 150), (400, 430), (210, 670)),
        stroke((390, 400), (390, 850)),
        stroke((390, 410), (750, 410), (750, 820), (690, 860)),
        stroke((400, 580), (740, 580)), stroke((400, 730), (740, 730))]),
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
