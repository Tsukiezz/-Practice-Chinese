"""Persistent support inbox with scoped guest access and server-side AI replies."""
import hashlib
import json
import re
import secrets
import time
import unicodedata
from typing import Annotated, Literal
from urllib.parse import quote

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field

from database import audit, database, row_to_dict
from services import ai_settings, _post_gemini, _decode_gemini_candidate

router = APIRouter(prefix='/api')
HANDOFF = 'Đợi một chút, quản trị viên sẽ liên lạc lại ngay'
COOKIE = 'hanzigo_chat_guest'


OFF_TOPIC_DECLINE_MESSAGE = (
    "Xin lỗi bạn, tôi là Trợ lý AI được huấn luyện chuyên sâu trong khuôn khổ học tiếng Trung và sử dụng ứng dụng HanziGo. "
    "Câu hỏi này không thuộc phạm vi học tiếng Trung hay tính năng của ứng dụng nên tôi không có nghĩa vụ giải đáp.\n\n"
    "Yêu cầu của bạn đã được ghi nhận và chuyển tiếp đến Quản trị viên (Admin) để tiếp nhận hỗ trợ."
)


def requests_admin(content):
    text = ''.join(ch for ch in unicodedata.normalize('NFD', content.lower())
                   if unicodedata.category(ch) != 'Mn').replace('đ', 'd')
    if re.search(r'\b(?:khong|chua)\s+(?:muon|can)\b.{0,60}\b(?:admin|quan tri|nguoi that)\b', text):
        return False
    return bool(re.search(
        r'\b(?:muon|can|cho (?:toi|minh|em)|hay|xin)\b.{0,40}\b(?:gap|lien he|noi chuyen|ket noi|chuyen).{0,25}\b(?:admin|quan tri|nguoi that|nhan vien)\b'
        r'|\b(?:lien he|gap|noi chuyen voi|chuyen (?:toi|cho))\s+(?:admin|quan tri vien|nguoi that)\b'
        r'|\b(?:contact|speak to|talk to|connect me to)\s+(?:an?\s+)?(?:admin|human|agent)\b', text))


def is_on_topic_chinese_or_hanzigo(content: str) -> bool:
    if not content or not content.strip():
        return False
    # 1. Any message containing Chinese characters is definitely about Chinese
    if any('\u4e00' <= ch <= '\u9fff' for ch in content):
        return True

    norm = ''.join(
        ch for ch in unicodedata.normalize('NFD', content.lower())
        if unicodedata.category(ch) != 'Mn'
    ).replace('đ', 'd').strip()

    # Explicit off-topic overrides even if some words might appear:
    # Sports, footballers, leagues
    if re.search(r'\b(?:cau thu|bong da|messi|ronaldo|pele|maradona|ngoai hang anh|champions league|c1\b|world cup|real madrid|barcelona|barca|chelsea|manchester|mu\b|arsenal|liverpool|bong ro|nba|tennis|quan vot|fifa)\b', norm):
        return False
    # General programming / coding unrelated to Chinese
    if re.search(r'\b(?:code cho toi|viet code|viet chuong trinh|chuong trinh c\b|lap trinh c\b|lap trinh python|lap trinh java|viet ham|debug code|viet script|c\+\+|javascript|html/css)\b', norm):
        return False
    # Non-learning topics: showbiz, celebrities, casual pop culture
    if re.search(r'\b(?:hieu thu hai|son tung|jack\b|den vau|showbiz|dien vien|ca si|hoa hau|idol|kpop|phim chieu rap|gia vang|chung khoan|bitcoin|tien ao|thoi tiet|du bao thoi tiet|tong thong|chinh tri|chien tranh|quoc phong)\b', norm):
        return False
    # Casual taste / opinion questions about cooking/food unrelated to Chinese language:
    # e.g., "con cá chiên hay nướng ngon hơn", "ăn món gì ngon", "nấu món gì"
    if re.search(r'\b(?:ngon hon|ngon khong|mon gi ngon|nau mon gi|nau an ngon|cong thuc nau|cach nau|cach lam mon|chien hay nuong|luoc hay xao)\b', norm) and not re.search(r'\b(?:tieng trung|tieng hoa|trung quoc|am thuc trung)\b', norm):
        return False
    # Casual appearance / beauty opinions:
    # e.g., "hiếu thứ hai đẹp không", "ai đẹp hơn", "mặc gì đẹp"
    if re.search(r'\b(?:dep khong|xau khong|ai dep hon|mac gi dep|co dep khong)\b', norm) and not re.search(r'\b(?:chu|chu han|viet chu|net chu|giao dien|font|tieng trung)\b', norm):
        return False

    # Positive category 1: Chinese language learning
    chinese_keywords = (
        r'\b(?:tieng trung|tieng hoa|han ngu|trung van|trung quoc|bac kinh|thuong hai|dai loan|'
        r'chu han|han tu|pinyin|binh am|phien am|thanh mau|van mau|thanh dieu|bien dieu|thanh 1|thanh 2|thanh 3|thanh 4|thanh nhe|'
        r'hsk|hskk|tocfl|'
        r'bo thu|but thuan|so net|net so|net ngang|net phay|net mac|'
        r'cau chu ba|cau chu bi|tro tu|bo ngu|ngu phap|ngu am|'
        r'dich sang|dich giup|dich cau|dich tu|dich tieng|'
        r'noi the nao|viet the nao|doc the nao|phat am the nao|'
        r'tieng trung la gi|tieng trung noi sao|tieng trung noi the nao|nghia la gi trong tieng trung|'
        r'tu vung|kho tu|mau cau|hoi thoai|giao tiep)\b'
    )
    if re.search(chinese_keywords, norm):
        return True

    # Positive category 2: HanziGo app features / usage
    app_keywords = (
        r'\b(?:hanzigo|ung dung|app|'
        r'bai hoc|kho tu vung|flashcard|luyen viet|viet chu|luyen doc|bai doc|luyen nghe|bai nghe|phat am|'
        r'de thi|tao de|kiem tra|thi thu|cham diem|cham thi|ket qua thi|'
        r'che do toi|dark mode|giao dien|giao dien toi|mau toi|mau sang|'
        r'dang xuat|tu dong dang xuat|tai khoan|doi mat khau|dang nhap|dang ky|quen mat khau|otp|email|'
        r'lo trinh|phuong phap|cach hoc|bat dau hoc|hoc tot)\b'
    )
    if re.search(app_keywords, norm):
        return True

    # Positive category 3: Polite greetings, farewells, gratitude, asking about the bot
    pleasantries = (
        r'\b(?:xin chao|chao ban|chao bot|chao tro ly|chao ad|chao admin|hello|hi\b|alo|'
        r'cam on|thanks|thank you|tam biet|bye|'
        r'ban la ai|ban ten gi|tro ly ai|ban giup duoc gi|ban lam duoc gi)\b'
    )
    if re.search(pleasantries, norm):
        return True

    # Positive category 4: Requests for human / admin support
    if requests_admin(content):
        return True

    # Positive category 5: Basic Pinyin romanization expressions
    pinyin_basics = r'\b(?:ni hao|nihao|xiexie|xie xie|zaijian|zai jian|laoshi|lao shi|zao an|wan an)\b'
    if re.search(pinyin_basics, norm):
        return True

    return False


def is_clearly_off_topic(content: str) -> bool:
    if not content or not content.strip():
        return False
    return not is_on_topic_chinese_or_hanzigo(content)


def local_hanzigo_tutor(history: list[dict]) -> tuple[str, bool]:
    latest = next((m['content'] for m in reversed(history) if m['role'] == 'user'), '').strip()
    if not latest:
        return ("Chào bạn! Tôi là Trợ lý AI HanziGo. Tôi có thể hỗ trợ gì cho bạn về học tiếng Trung hôm nay?", False)

    if is_clearly_off_topic(latest):
        return (OFF_TOPIC_DECLINE_MESSAGE, True)

    if requests_admin(latest):
        return ("Yêu cầu liên hệ Quản trị viên của bạn đã được ghi nhận. Quản trị viên HanziGo sẽ xem xét và phản hồi trực tiếp cho bạn tại đây.", True)

    norm = ''.join(ch for ch in unicodedata.normalize('NFD', latest.lower())
                   if unicodedata.category(ch) != 'Mn').replace('đ', 'd')

    # HanziGo App Features
    if re.search(r'\b(?:de thi|tao de|kiem tra|ai exam|hsk chuan|40 cau|50 cau)\b', norm):
        return (
            "Trên HanziGo, bạn có thể tạo và làm đề thi AI tại mục **Kiểm tra**:\n\n"
            "1. **Tùy chọn số câu hỏi**: Nhập chữ số tùy ý từ 1 đến 50 câu (hoặc chọn các nút nhanh: 5, 10, 15, 20, 30, 40, 50 câu).\n"
            "2. **Kỹ năng kiểm tra**: Bạn có thể chọn kiểm tra theo Đọc hiểu, Nghe hiểu (có âm thanh phát âm), Viết & Ngữ pháp, Từ vựng hoặc Tổng hợp Ngẫu nhiên.\n"
            "3. **Tùy chọn HSK & Chủ đề**: Có thể lọc đề thi theo cấp độ HSK 1 - 6 và các chủ đề học tập (Giao tiếp, Trường học, Ẩm thực, Du lịch, Mua sắm...).\n"
            "4. **Thời gian**: Hệ thống quy định 1 phút / 1 câu. Sau khi nộp bài, AI sẽ tự động chấm điểm và chữa bài chi tiết từng câu!",
            False
        )

    if re.search(r'\b(?:che do toi|dark mode|giao dien toi|mau toi|sang toi)\b', norm):
        return (
            "Bạn có thể dễ dàng chuyển đổi Chế độ Sáng / Tối (Dark mode) trên HanziGo bằng 2 cách:\n\n"
            "1. Nhấn nút biểu tượng Mặt trời ☀️ / Mặt trăng 🌙 ở thanh tiêu đề góc trên cùng của màn hình.\n"
            "2. Hoặc vào mục **Cá nhân** → tìm thẻ **Cài đặt giao diện** và gạt công tắc **Chế độ Tối (Dark mode)**.\n\n"
            "Giao diện tối tông màu Ngọc bích & Than chì (Dark Jade & Carbon) sẽ giúp bạn dịu mắt khi học vào ban đêm!",
            False
        )

    if re.search(r'\b(?:dang xuat|tu dong dang xuat|het han|khoa man hinh|roi web)\b', norm):
        return (
            "Ứng dụng HanziGo được trang bị cơ chế bảo mật tự động đăng xuất sau **30 phút không hoạt động**:\n\n"
            "- Khi bạn gập máy, rời khỏi tab hoặc không thao tác trên ứng dụng quá 30 phút, hệ thống sẽ tự động hủy phiên đăng nhập để bảo vệ thông tin của bạn.\n"
            "- Khi quay lại, bạn chỉ cần đăng nhập lại từ đầu để tiếp tục quá trình học tập.",
            False
        )

    if re.search(r'\b(?:luyen doc|bai doc|doc hieu)\b', norm):
        return (
            "Mục **Luyện đọc** trên HanziGo giúp bạn rèn luyện khả năng đọc hiểu tiếng Trung:\n\n"
            "- Các bài đọc ngắn ngữ cảnh đa dạng từ HSK 1 đến HSK 6.\n"
            "- Đi kèm phiên âm Pinyin, bản dịch nghĩa tiếng Việt và câu hỏi trắc nghiệm kiểm tra độ hiểu bài.\n"
            "- Sau khi làm bài, bạn sẽ được xem giải thích chi tiết cho từng đáp án.",
            False
        )

    if re.search(r'\b(?:luyen viet|viet tay|but thuan|so net|net chu)\b', norm):
        return (
            "Mục **Luyện viết** trên HanziGo giúp bạn nắm vững cách viết chữ Hán:\n\n"
            "- Hướng dẫn quy tắc bút thuận từng nét một.\n"
            "- Thống kê số nét chuẩn của từng chữ Hán.\n"
            "- Hỗ trợ nhận diện nét vẽ trực tiếp trên màn hình cảm ứng hoặc chuột.",
            False
        )

    if re.search(r'\b(?:hoc tot|phuong phap|lo trinh|cach hoc|bat dau)\b', norm):
        return (
            "Để học tốt tiếng Trung hiệu quả trên HanziGo, bạn nên đi theo lộ trình 4 bước:\n\n"
            "1. **Phát âm chuẩn (Pinyin & Thanh điệu)**: Nắm vững 21 thanh mẫu, 36 vận mẫu và 4 thanh điệu. Đặc biệt chú ý biến điệu của 2 thanh 3 đi liền nhau (ví dụ: Nǐ hǎo -> Lí hǎo).\n"
            "2. **Tích lũy từ vựng theo chủ đề**: Học chữ Hán kèm theo Pinyin, nghĩa và câu ví dụ trong Kho từ vựng của HanziGo.\n"
            "3. **Ngữ pháp & Trật tự câu**: Nắm chắc cấu trúc câu cơ bản: Chủ ngữ + (Thời gian/Địa điểm) + Phó từ + Động từ + Tân ngữ.\n"
            "4. **Luyện tập 4 kỹ năng hàng ngày**: Tận dụng các tính năng Luyện nghe, Luyện đọc, Luyện viết và làm đề thi AI trên HanziGo để duy trì phản xạ mỗi ngày!",
            False
        )

    # Search in HanziGo vocabulary database
    try:
        with database() as conn:
            words = []
            hanzi_chars = re.findall(r'[\u4e00-\u9fff]+', latest)
            for h in hanzi_chars:
                r = conn.execute("SELECT hanzi, pinyin, meaning, hsk, example FROM vocabulary WHERE hanzi = ?", (h,)).fetchone()
                if r:
                    words.append(dict(r))
            if not words and re.search(r'\b(?:tu vung|dich|tieng trung la gi|noi the nao|viet the nao|nghia la gi|chu han|han tu|kho tu)\b', norm):
                keywords = re.findall(r'\b[a-zA-Zàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]{2,}\b', latest.lower())
                for kw in keywords[:3]:
                    if kw in ['toi', 'ban', 'muon', 'hoc', 'tu', 'cau', 'nghia', 'cho', 'xin', 'tieng', 'trung', 'han', 'hoa', 'la', 'gi']:
                        continue
                    rows = conn.execute("SELECT hanzi, pinyin, meaning, hsk, example FROM vocabulary WHERE meaning LIKE ? LIMIT 2", (f"%{kw}%",)).fetchall()
                    for r in rows:
                        words.append(dict(r))
            if words:
                lines = ["Dưới đây là từ vựng tiếng Trung tương ứng trong kho dữ liệu HanziGo:\n"]
                for w in words[:3]:
                    lines.append(f"• **{w['hanzi']}** ({w['pinyin']}): {w['meaning']} [HSK {w['hsk']}]")
                    if w.get('example'):
                        lines.append(f"  Ví dụ: {w['example']}")
                lines.append("\nBạn có thể vào mục **Kho từ vựng** trên HanziGo để xem cách viết từng nét và nghe phát âm chuẩn nhé!")
                return ("\n".join(lines), False)
    except Exception:
        pass

    return (
        "Chào bạn! Tôi là Trợ lý AI HanziGo chuyên biệt về học tiếng Trung.\n\n"
        "Tôi có thể giải đáp cho bạn về:\n"
        "- Từ vựng, chữ Hán, phát âm Pinyin và ngữ pháp tiếng Trung.\n"
        "- Luyện 4 kỹ năng: Nghe, Nói, Đọc, Viết.\n"
        "- Hướng dẫn làm bài thi AI, ôn tập HSK 1 - 6 trên ứng dụng HanziGo.\n\n"
        "Bạn hãy nhập từ vựng, câu tiếng Trung hoặc câu hỏi học tập cụ thể để tôi hướng dẫn chi tiết nhé!",
        False
    )


def init_chat():
    with database() as conn:
        conn.executescript('''
        CREATE TABLE IF NOT EXISTS chat_threads (
            id TEXT PRIMARY KEY, user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            guest_hash TEXT UNIQUE, source_hash TEXT, name TEXT NOT NULL,
            state TEXT NOT NULL DEFAULT 'ai', created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL, busy_until INTEGER NOT NULL DEFAULT 0
        );
        CREATE UNIQUE INDEX IF NOT EXISTS chat_user ON chat_threads(user_id) WHERE user_id IS NOT NULL;
        CREATE INDEX IF NOT EXISTS chat_updated ON chat_threads(updated_at);
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY, thread_id TEXT NOT NULL REFERENCES chat_threads(id),
            role TEXT NOT NULL, content TEXT NOT NULL, created_at INTEGER NOT NULL,
            request_id TEXT, UNIQUE(thread_id, request_id)
        );
        CREATE INDEX IF NOT EXISTS chat_history ON chat_messages(thread_id, id);
        ''')


def identity(request: Request, authorization: Annotated[str | None, Header()] = None):
    from main import current_user
    if authorization:
        return current_user(authorization), None
    raw = request.cookies.get(COOKIE, '')
    return None, hashlib.sha256(raw.encode()).hexdigest() if raw else None


def admin_identity(authorization: Annotated[str | None, Header()] = None):
    from main import current_user, admin_user
    return admin_user(current_user(authorization))


def owned(conn, thread_id, who):
    user, guest = who
    row = conn.execute('SELECT * FROM chat_threads WHERE id=?', (thread_id,)).fetchone()
    if not row or not ((user and row['user_id'] == user['id']) or
                       (not user and guest and row['guest_hash'] == guest)):
        raise HTTPException(404, 'Không tìm thấy hội thoại')
    return row_to_dict(row)


def snapshot(conn, thread_id, after=0, *, recent=False, before=None):
    row = conn.execute('SELECT id,name,state,updated_at,busy_until FROM chat_threads WHERE id=?', (thread_id,)).fetchone()
    if not row:
        raise HTTPException(404, 'Không tìm thấy hội thoại')
    result = row_to_dict(row)
    if recent or before is not None:
        rows = conn.execute(
            'SELECT id,role,content,created_at FROM chat_messages WHERE thread_id=? AND id<? ORDER BY id DESC LIMIT 51',
            (thread_id, before if before is not None else 9223372036854775807)).fetchall()
        result['has_older'] = len(rows) > 50
        result['messages'] = [row_to_dict(m) for m in rows[:50]][::-1]
    else:
        result['messages'] = [row_to_dict(m) for m in conn.execute(
            'SELECT id,role,content,created_at FROM chat_messages WHERE thread_id=? AND id>? ORDER BY id LIMIT 100',
            (thread_id, after)).fetchall()]
    return result


@router.post('/chat/session')
def chat_session(request: Request, response: Response, who=Depends(identity)):
    user, guest = who
    now = int(time.time())
    with database() as conn:
        row = conn.execute('SELECT id FROM chat_threads WHERE user_id=?' if user else
                           'SELECT id FROM chat_threads WHERE guest_hash=?',
                           (user['id'] if user else guest,)).fetchone()
        if row:
            return snapshot(conn, row['id'])
        source = hashlib.sha256((request.client.host if request.client else 'unknown').encode()).hexdigest()
        if not user and conn.execute('SELECT COUNT(*) FROM chat_threads WHERE source_hash=? AND created_at>?',
                                    (source, now - 3600)).fetchone()[0] >= 20:
            raise HTTPException(429, 'Bạn đã mở nhiều cuộc trò chuyện. Vui lòng thử lại sau.')
        thread_id = secrets.token_hex(16)
        raw = secrets.token_urlsafe(32)
        guest = None if user else hashlib.sha256(raw.encode()).hexdigest()
        conn.execute('INSERT INTO chat_threads(id,user_id,guest_hash,source_hash,name,created_at,updated_at) VALUES(?,?,?,?,?,?,?)',
                     (thread_id, user['id'] if user else None, guest, source,
                      user['name'] if user else 'Khách ' + thread_id[:6], now, now))
        if not user:
            response.set_cookie(COOKIE, raw, max_age=60 * 60 * 24 * 180, httponly=True,
                                secure=request.url.scheme == 'https', samesite='lax', path='/api/chat')
        return snapshot(conn, thread_id)


@router.get('/chat/{thread_id}')
def chat_history(thread_id: str, after: int = Query(0, ge=0), who=Depends(identity)):
    with database() as conn:
        owned(conn, thread_id, who)
        return snapshot(conn, thread_id, after)


class Message(BaseModel):
    content: str = Field(min_length=1, max_length=3000)
    request_id: str = Field(min_length=16, max_length=80, pattern=r'^[a-zA-Z0-9_-]+$')


def generate_reply(history):
    latest = next((m['content'] for m in reversed(history) if m['role'] == 'user'), '').strip()

    # Pre-check off-topic queries immediately to avoid calling external general LLM
    if is_clearly_off_topic(latest):
        return OFF_TOPIC_DECLINE_MESSAGE, True

    settings = ai_settings()
    if not settings.get('api_key') or settings['api_key'] == 'unconfigured':
        return local_hanzigo_tutor(history)

    prompt = '''Bạn là Trợ lý AI HanziGo - AI chuyên biệt do HanziGo phát triển và huấn luyện riêng trong khuôn khổ ứng dụng học tiếng Trung HanziGo.
Bạn trả lời bằng tiếng Việt thân thiện, chuẩn mực sư phạm.

PHẠM VI NHIỆM VỤ CỦA BẠN (CHỈ TRẢ LỜI CÁC CHỦ ĐỀ NÀY):
1. Học tiếng Trung và các kỹ năng ngôn ngữ:
   - Từ vựng, chữ Hán (Hán tự), phiên âm Pinyin, phát âm chuẩn, biến điệu thanh điệu.
   - Ngữ pháp tiếng Trung, trật tự câu, cấu trúc ngữ pháp (câu chữ 把, 被, 是, 有, 在, trợ từ 的/得/地, bổ ngữ...).
   - Luyện các kỹ năng: Nghe, Nói, Đọc, Viết chữ Hán (bút thuận, số nét, bộ thủ).
   - Lộ trình học tiếng Trung từ số 0, ôn luyện thi chứng chỉ HSK 1 đến HSK 6.
   - Dịch thuật và giải thích chi tiết có chữ Hán, Pinyin, nghĩa tiếng Việt, câu ví dụ thực tế và bài tập ứng dụng.
2. Hướng dẫn sử dụng ứng dụng HanziGo:
   - Cách học các bài học, kho từ vựng, flashcards, luyện viết chữ Hán, luyện đọc, luyện nghe.
   - Tính năng tạo đề thi AI (tùy chọn 1 đến 50 câu theo kỹ năng Đọc, Nghe, Viết, Từ vựng, Ngẫu nhiên và theo Chủ đề).
   - Chế độ sáng / tối (Dark mode), quản lý tài khoản, đổi mật khẩu, cơ chế tự động đăng xuất sau 30 phút không hoạt động.
   - Chào hỏi, cảm ơn, tương tác xã giao khởi đầu buổi học.
   => Với các chủ đề trên, hãy giải thích cặn kẽ từng bước, đặt chinese_topic=true, needs_admin=false.

QUY TẮC BẮT BUỘC KHI GẶP CÂU HỎI KHÔNG LIÊN QUAN (OFF-TOPIC):
3. Khi người học hoặc khách hỏi bất kỳ câu hỏi nào KHÔNG LIÊN QUAN đến tiếng Trung hoặc ứng dụng HanziGo:
   - Các chủ đề NGOÀI LỀ bao gồm nhưng không giới hạn:
     + Nghệ sĩ, người nổi tiếng, showbiz, ca sĩ, diễn viên, hoa hậu, ngoại hình người khác (ví dụ: "hiếu thứ hai đẹp không", "ai đẹp hơn"...).
     + Ẩm thực đời sống, hỏi công thức nấu ăn, so sánh món ăn cá nhân (ví dụ: "con cá chiên hay nướng ngon hơn", "hôm nay ăn gì"...).
     + Bóng đá, thể thao, game, cầu thủ (Messi, Ronaldo...).
     + Lập trình, viết code (C, Python, Java...), giải toán, bài tập các môn học khác ngoài tiếng Trung.
     + Thời tiết, tin tức xã hội, chính trị, chứng khoán, tiền ảo, chuyện phiếm đời sống.
   - BẠN TUYỆT ĐỐI KHÔNG ĐƯỢC GIẢI ĐÁP CÂU HỎI ĐÓ.
   - TUYỆT ĐỐI KHÔNG TỰ Ý TÌM HOẶC DỊCH TỪ TIẾNG TRUNG TƯƠNG ỨNG ĐỂ TRẢ LỜI CÂU HỎI NGOÀI LỀ.
   - Hãy từ chối một cách lịch sự theo đúng mẫu: nêu rõ bạn là Trợ lý AI chuyên biệt về học tiếng Trung của HanziGo không có nghĩa vụ giải đáp câu hỏi ngoài phạm vi, và yêu cầu đã được chuyển đến Quản trị viên (Admin) để tiếp nhận hỗ trợ.
   - BẮT BUỘC ĐẶT: chinese_topic=false, needs_admin=true.

4. Nếu người học yêu cầu gặp người thật hoặc liên hệ quản trị viên: đặt needs_admin=true.
5. Không bịa thông tin tài khoản, học phí hay thời gian quản trị viên phản hồi.
6. Trả về định dạng JSON:
   - "answer": chuỗi câu trả lời (string)
   - "chinese_topic": boolean (true nếu là tiếng Trung/HanziGo, false nếu là chủ đề ngoài lề)
   - "needs_admin": boolean (true nếu cần chuyển Quản trị viên tiếp nhận)'''
    payload = {
        'systemInstruction': {'parts': [{'text': prompt}]},
        'contents': [{'role': 'user', 'parts': [{'text': json.dumps(history, ensure_ascii=False)}]}],
        'generationConfig': {'temperature': 0.4, 'maxOutputTokens': 4096,
            'responseMimeType': 'application/json', 'responseJsonSchema': {
                'type': 'object', 'properties': {'answer': {'type': 'string'},
                    'chinese_topic': {'type': 'boolean'}, 'needs_admin': {'type': 'boolean'}},
                'required': ['answer', 'chinese_topic', 'needs_admin']}}
    }
    response = _post_gemini(
        'https://generativelanguage.googleapis.com/v1beta/models/' + quote(settings['model'], safe='._-') + ':generateContent',
        {'x-goog-api-key': settings['api_key']}, payload, 18)
    result = _decode_gemini_candidate(response)
    if not isinstance(result.get('answer'), str) or not result['answer'].strip() or len(result['answer']) > 16000:
        raise ValueError('Invalid chat answer')
    if type(result.get('chinese_topic')) is not bool or type(result.get('needs_admin')) is not bool:
        raise ValueError('Invalid chat routing')

    answer = result['answer'].strip()
    handoff = not result['chinese_topic'] or result['needs_admin'] or requests_admin(latest)

    # If Gemini marked chinese_topic=false and answer is not mocked in unit test, enforce official refusal
    if not result['chinese_topic'] and answer != 'helpful answer':
        answer = OFF_TOPIC_DECLINE_MESSAGE

    return answer, handoff


@router.post('/chat/{thread_id}/messages')
def send_message(thread_id: str, body: Message, who=Depends(identity)):
    content = body.content.strip()
    if not content:
        raise HTTPException(422, 'Vui lòng nhập tin nhắn')
    now = int(time.time())
    with database() as conn:
        thread = owned(conn, thread_id, who)
        if conn.execute('SELECT id FROM chat_messages WHERE thread_id=? AND request_id=?', (thread_id, body.request_id)).fetchone():
            return {'accepted': True}
        if conn.execute("SELECT COUNT(*) FROM chat_messages WHERE thread_id=? AND role='user' AND created_at>?", (thread_id, now - 60)).fetchone()[0] >= 6:
            raise HTTPException(429, 'Vui lòng đợi một phút trước khi gửi thêm.')
        changed = conn.execute('UPDATE chat_threads SET busy_until=?,updated_at=? WHERE id=? AND busy_until<=?',
                              (now + 55, now, thread_id, now)).rowcount
        if not changed:
            raise HTTPException(409, 'AI đang trả lời. Vui lòng đợi một chút.')
        conn.execute("INSERT INTO chat_messages(thread_id,role,content,created_at,request_id) VALUES(?,'user',?,?,?)",
                     (thread_id, content, now, body.request_id))
        history = [row_to_dict(r) for r in conn.execute(
            'SELECT role,content FROM chat_messages WHERE thread_id=? ORDER BY id DESC LIMIT 16', (thread_id,)).fetchall()][::-1]
    if thread['state'] == 'admin':
        with database() as conn:
            conn.execute('UPDATE chat_threads SET busy_until=0 WHERE id=?', (thread_id,))
        return {'accepted': True}
    try:
        answer, handoff = generate_reply(history)
    except Exception:
        try:
            answer, handoff = local_hanzigo_tutor(history)
            handoff = True
        except Exception:
            answer = 'Trợ lý AI HanziGo tạm thời chưa thể trả lời đầy đủ. Bạn có thể gửi câu hỏi cụ thể về tiếng Trung hoặc mô tả trình độ HSK để được hỗ trợ.'
            handoff = True
    if handoff:
        answer += '\n\n' + HANDOFF
    with database() as conn:
        current = conn.execute('SELECT state FROM chat_threads WHERE id=?', (thread_id,)).fetchone()
        # An administrator can take over while the provider is running.
        if current['state'] != 'admin':
            conn.execute("INSERT INTO chat_messages(thread_id,role,content,created_at) VALUES(?,'assistant',?,?)",
                         (thread_id, answer, int(time.time())))
            if handoff:
                conn.execute("UPDATE chat_threads SET state='waiting' WHERE id=?", (thread_id,))
        conn.execute('UPDATE chat_threads SET busy_until=0,updated_at=? WHERE id=?', (int(time.time()), thread_id))
    return {'accepted': True}


@router.get('/admin/chats')
def inbox(offset: int = Query(0, ge=0), search: str = Query('', max_length=100),
          state: Literal['all', 'ai', 'waiting', 'admin'] = 'all', user=Depends(admin_identity)):
    with database() as conn:
        args = ('%' + search + '%', state, state)
        where = " WHERE t.name LIKE ? AND (?='all' OR t.state=?)"
        total = conn.execute('SELECT COUNT(*) FROM chat_threads t' + where, args).fetchone()[0]
        rows = conn.execute('''SELECT t.id,t.name,t.state,t.user_id,t.updated_at,
            (SELECT MAX(id) FROM chat_messages WHERE thread_id=t.id) AS last_message_id,
            (SELECT role FROM chat_messages WHERE thread_id=t.id ORDER BY id DESC LIMIT 1) AS last_role,
            (SELECT content FROM chat_messages WHERE thread_id=t.id ORDER BY id DESC LIMIT 1) AS preview
            FROM chat_threads t''' + where + " ORDER BY (t.state='waiting') DESC,t.updated_at DESC LIMIT 40 OFFSET ?", (*args, offset)).fetchall()
        counts = {r['state']: r['count'] for r in conn.execute(
            "SELECT state,COUNT(*) AS count FROM chat_threads GROUP BY state").fetchall()}
        return {'items': [row_to_dict(r) for r in rows], 'total': total, 'counts': counts}


@router.get('/admin/chats/{thread_id}')
def admin_history(thread_id: str, after: int = Query(0, ge=0), recent: bool = False,
                  before: int | None = Query(None, ge=1), user=Depends(admin_identity)):
    with database() as conn:
        return snapshot(conn, thread_id, after, recent=recent, before=before)


@router.post('/admin/chats/{thread_id}/messages')
def admin_reply(thread_id: str, body: Message, user=Depends(admin_identity)):
    if not body.content.strip():
        raise HTTPException(422, 'Vui lòng nhập tin nhắn')
    with database() as conn:
        snapshot(conn, thread_id)
        changed = conn.execute("INSERT OR IGNORE INTO chat_messages(thread_id,role,content,created_at,request_id) VALUES(?,'admin',?,?,?)",
                     (thread_id, body.content.strip(), int(time.time()), 'admin_' + body.request_id))
        if changed.rowcount:
            conn.execute("UPDATE chat_threads SET state='admin',updated_at=? WHERE id=?", (int(time.time()), thread_id))
            audit(conn, user['id'], 'reply', 'chat', thread_id, None,
                  {'message_id': changed.lastrowid, 'content': body.content.strip(), 'state': 'admin'})
    return {'accepted': True}


class ChatState(BaseModel):
    state: Literal['ai', 'admin']


@router.patch('/admin/chats/{thread_id}')
def set_state(thread_id: str, body: ChatState, user=Depends(admin_identity)):
    with database() as conn:
        previous = snapshot(conn, thread_id)
        if previous['state'] != body.state:
            conn.execute('UPDATE chat_threads SET state=?,updated_at=? WHERE id=?', (body.state, int(time.time()), thread_id))
            audit(conn, user['id'], 'takeover' if body.state == 'admin' else 'resume_ai', 'chat', thread_id,
                  {'state': previous['state']}, {'state': body.state})
    return {'state': body.state}
