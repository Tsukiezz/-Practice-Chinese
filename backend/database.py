"""SQLite storage shared by Admin and learner integrations."""
import json
import os
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(os.environ.get("DATABASE_PATH", Path(__file__).with_name("hanzi_go.db")))


@contextmanager
def database():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def audit(conn, actor, action, entity, entity_id, before=None, after=None):
    conn.execute(
        "INSERT INTO audit_logs(actor_id,action,entity,entity_id,before_json,after_json,created_at) VALUES(?,?,?,?,?,?,?)",
        (actor, action, entity, str(entity_id), json.dumps(before, ensure_ascii=False),
         json.dumps(after, ensure_ascii=False), int(time.time())),
    )


def init_db():
    with database() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL, salt TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student' CHECK(role IN ('student','admin')),
            is_active INTEGER NOT NULL DEFAULT 1, created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sessions (
            token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
            expires_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS vocabulary (
            id INTEGER PRIMARY KEY, hanzi TEXT NOT NULL UNIQUE, pinyin TEXT NOT NULL,
            meaning TEXT NOT NULL, hsk INTEGER NOT NULL CHECK(hsk BETWEEN 1 AND 6),
            example TEXT NOT NULL DEFAULT '', audio_url TEXT NOT NULL DEFAULT '',
            strokes_json TEXT NOT NULL DEFAULT '[]', version INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY, title TEXT NOT NULL, hsk INTEGER NOT NULL CHECK(hsk BETWEEN 1 AND 6),
            status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','published','hidden')),
            duration_minutes INTEGER NOT NULL, questions_json TEXT NOT NULL,
            version INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS exam_words (
            exam_id INTEGER NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
            word_id INTEGER NOT NULL REFERENCES vocabulary(id) ON DELETE RESTRICT,
            PRIMARY KEY(exam_id,word_id)
        );
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
            exam_id INTEGER REFERENCES exams(id) ON DELETE RESTRICT,
            kind TEXT NOT NULL CHECK(kind IN ('exam','handwriting','writing')),
            content TEXT NOT NULL, score REAL NOT NULL CHECK(score BETWEEN 0 AND 100),
            original_score REAL NOT NULL, feedback TEXT NOT NULL DEFAULT '',
            graded_by TEXT NOT NULL CHECK(graded_by IN ('automatic','ai','admin')),
            version INTEGER NOT NULL DEFAULT 1, created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS score_overrides (
            id INTEGER PRIMARY KEY, result_id INTEGER NOT NULL REFERENCES results(id),
            admin_id INTEGER NOT NULL REFERENCES users(id), old_score REAL NOT NULL,
            new_score REAL NOT NULL, reason TEXT NOT NULL, created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS ai_config (
            id INTEGER PRIMARY KEY CHECK(id=1), model TEXT NOT NULL,
            system_prompt TEXT NOT NULL, temperature REAL NOT NULL, max_tokens INTEGER NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 0, version INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS ai_usage (
            id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id), module TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('success','error')), created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY, actor_id INTEGER NOT NULL REFERENCES users(id),
            action TEXT NOT NULL, entity TEXT NOT NULL, entity_id TEXT NOT NULL,
            before_json TEXT NOT NULL, after_json TEXT NOT NULL, created_at INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS results_user ON results(user_id,created_at);
        CREATE INDEX IF NOT EXISTS sessions_user ON sessions(user_id);
        CREATE TABLE IF NOT EXISTS appeals (
            id INTEGER PRIMARY KEY, result_id INTEGER NOT NULL REFERENCES results(id),
            user_id INTEGER NOT NULL REFERENCES users(id), reason TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','resolved')),
            response TEXT NOT NULL DEFAULT '', reviewer_id INTEGER REFERENCES users(id),
            created_at INTEGER NOT NULL, resolved_at INTEGER,
            version INTEGER NOT NULL DEFAULT 1
        );
        CREATE UNIQUE INDEX IF NOT EXISTS appeals_pending ON appeals(result_id) WHERE status='pending';
        """)
        # Additive, idempotent migration: preserve existing accounts and sessions.
        if 'version' not in {row['name'] for row in conn.execute('PRAGMA table_info(users)')}:
            conn.execute('ALTER TABLE users ADD COLUMN version INTEGER NOT NULL DEFAULT 1')
        conn.execute("INSERT OR IGNORE INTO ai_config(id,model,system_prompt,temperature,max_tokens) VALUES(1,?,?,0.2,1000)",
                     ("configure-your-model", "Bạn là giáo viên tiếng Trung. Trả điểm 0–100 và nhận xét bằng tiếng Việt."))
