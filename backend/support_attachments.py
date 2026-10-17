"""Private support files, stored durably alongside chat history in SQLite/libSQL."""
import base64
import binascii
import io
import re
import zipfile
from PIL import Image, UnidentifiedImageError

from fastapi import HTTPException
from pydantic import BaseModel, Field

MAX_FILE_BYTES = 2 * 1024 * 1024


class AttachmentInput(BaseModel):
    filename: str = Field(min_length=1, max_length=180)
    data_base64: str = Field(min_length=1, max_length=2796204)


def validate_attachment(file: AttachmentInput | None):
    if file is None:
        return None
    name = re.sub(r'[\x00-\x1f\x7f]', '', file.filename.replace('\\', '/').split('/')[-1]).strip()
    extension = name.rsplit('.', 1)[-1].lower()
    types = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
             'webp': 'image/webp', 'pdf': 'application/pdf', 'txt': 'text/plain',
             'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}
    if extension not in types:
        raise HTTPException(422, 'Chỉ hỗ trợ PNG, JPG, WEBP, PDF, DOCX và TXT.')
    try:
        data = base64.b64decode(file.data_base64, validate=True)
    except (ValueError, binascii.Error):
        raise HTTPException(422, 'Dữ liệu tệp không hợp lệ.')
    if not data or len(data) > MAX_FILE_BYTES:
        raise HTTPException(413, 'Mỗi tệp phải có nội dung và không vượt quá 2 MB.')
    valid = False
    if extension == 'pdf':
        valid = data.startswith(b'%PDF-')
    elif extension == 'png':
        valid = data.startswith(b'\x89PNG\r\n\x1a\n')
    elif extension in ('jpg', 'jpeg'):
        valid = data.startswith(b'\xff\xd8\xff')
    elif extension == 'webp':
        valid = data.startswith(b'RIFF') and data[8:12] == b'WEBP'
    elif extension == 'txt':
        try:
            data.decode('utf-8-sig')
            valid = b'\x00' not in data
        except UnicodeError:
            pass
    elif extension == 'docx':
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                valid = {'[Content_Types].xml', 'word/document.xml'} <= set(archive.namelist())
        except (zipfile.BadZipFile, ValueError):
            pass
    if not valid:
        raise HTTPException(422, 'Nội dung tệp không khớp định dạng. Vui lòng chọn lại tệp.')
    if types[extension].startswith('image/'):
        try:
            with Image.open(io.BytesIO(data)) as image:
                if image.width * image.height > 16_000_000 or image.width < 1 or image.height < 1:
                    raise ValueError('Image dimensions exceed limit')
                if Image.MIME.get(image.format) != types[extension]:
                    raise ValueError('Image type mismatch')
                image.verify()
        except (UnidentifiedImageError, OSError, ValueError, SyntaxError, Image.DecompressionBombError):
            raise HTTPException(422, 'Ảnh bị hỏng hoặc quá lớn. Chọn PNG/JPG/WEBP tối đa 16 triệu điểm ảnh.') from None
    return {'filename': name, 'content_type': types[extension], 'size': len(data),
            'data_base64': base64.b64encode(data).decode('ascii')}


def check_file_quota(conn, thread_id, file, now):
    if not file:
        return
    used = conn.execute('''SELECT COALESCE(SUM(a.size),0) FROM chat_attachments a
        JOIN chat_messages m ON m.id=a.message_id WHERE m.thread_id=? AND m.created_at>?''',
        (thread_id, now - 86400)).fetchone()[0]
    if used + file['size'] > 20 * 1024 * 1024:
        raise HTTPException(429, 'Hội thoại đã đạt giới hạn 20 MB tệp trong 24 giờ. Vui lòng thử lại sau.')


def save_attachment(conn, message_id, file):
    if file:
        conn.execute('''INSERT INTO chat_attachments(message_id,filename,content_type,size,data_base64)
            VALUES(?,?,?,?,?)''', (message_id, file['filename'], file['content_type'], file['size'], file['data_base64']))
