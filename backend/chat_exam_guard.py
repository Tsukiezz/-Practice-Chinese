"""Short-lived chat locks for active in-app exams, shared across sessions/tabs."""
import time
from fastapi import HTTPException
from pydantic import BaseModel, Field
from database import database


def owner(who):
    user, guest = who
    return 'user:' + str(user['id']) if user else ('guest:' + guest if guest else None)


def table(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS chat_exam_locks (
        owner TEXT NOT NULL, lease TEXT NOT NULL, expires_at INTEGER NOT NULL,
        PRIMARY KEY(owner, lease))''')


def blocked(conn, who):
    table(conn)
    return bool(conn.execute('SELECT 1 FROM chat_exam_locks WHERE owner=? AND expires_at>? LIMIT 1',
                            (owner(who), int(time.time()))).fetchone())


def require_chat_allowed(conn, who):
    if blocked(conn, who):
        raise HTTPException(423, 'Trợ lý AI bị khóa trong khi làm bài kiểm tra. Hãy nộp bài hoặc thoát bài trước.')


class ExamLock(BaseModel):
    lease: str = Field(min_length=8, max_length=100, pattern=r'^[a-zA-Z0-9_-]+$')
    active: bool


def update_lock(body, who):
    key = owner(who)
    if not key:
        raise HTTPException(401, 'Cần khởi tạo phiên trước khi làm bài.')
    with database() as conn:
        table(conn)
        now = int(time.time())
        conn.execute('DELETE FROM chat_exam_locks WHERE expires_at<=?', (now,))
        if body.active:
            conn.execute('''INSERT INTO chat_exam_locks VALUES(?,?,?)
                ON CONFLICT(owner,lease) DO UPDATE SET expires_at=excluded.expires_at''',
                (key, body.lease, now + 120))
        else:
            conn.execute('DELETE FROM chat_exam_locks WHERE owner=? AND lease=?', (key, body.lease))
        return {'blocked': blocked(conn, who)}
