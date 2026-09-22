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

print("Initializing student_ai_exams table on Turso...")
conn.executescript("""
    CREATE TABLE IF NOT EXISTS student_ai_exams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        title TEXT NOT NULL,
        content_type TEXT NOT NULL,
        hsk_level INTEGER,
        topic TEXT,
        question_count INTEGER NOT NULL,
        duration_minutes INTEGER NOT NULL,
        questions_json TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        score REAL,
        user_answers_json TEXT,
        ai_feedback_json TEXT,
        submitted_at INTEGER,
        created_at INTEGER NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_student_ai_exams_user ON student_ai_exams(user_id, status);
""")
conn.commit()

tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Turso tables count:", len(tables))
print("student_ai_exams ready:", 'student_ai_exams' in tables)

conn.close()
print("Migration completed successfully!")
