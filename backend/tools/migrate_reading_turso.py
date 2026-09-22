import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))

from dotenv import dotenv_values
from cloud_database import connect

secrets = dotenv_values(ROOT / '.vercel' / '.env.production.local')
db_url = secrets.get('TURSO_DATABASE_URL')
token = secrets.get('TURSO_AUTH_TOKEN')

if not db_url or not token:
    print("Missing TURSO credentials in .vercel/.env.production.local")
    sys.exit(1)

print("Connecting to Turso:", db_url)
conn = connect(db_url, auth_token=token)

print("Initializing student_reading_history table on Turso...")
conn.executescript("""
    CREATE TABLE IF NOT EXISTS student_reading_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        word_id INTEGER,
        hanzi TEXT NOT NULL,
        pinyin TEXT NOT NULL,
        meaning TEXT,
        accuracy_percent REAL NOT NULL,
        rating TEXT NOT NULL,
        spoken_text TEXT,
        errors_json TEXT NOT NULL DEFAULT '[]',
        corrections_json TEXT NOT NULL DEFAULT '[]',
        feedback_json TEXT NOT NULL DEFAULT '{}',
        audio_base64 TEXT,
        created_at INTEGER NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_reading_history_user
        ON student_reading_history(user_id, created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_reading_history_word
        ON student_reading_history(word_id);
""")
conn.commit()

tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Turso tables count:", len(tables))
print("student_reading_history ready:", 'student_reading_history' in tables)

conn.close()
print("Reading migration completed successfully on Turso!")
