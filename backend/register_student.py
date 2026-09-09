"""Register a student account in the local database."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding='utf-8')
from database import init_db, database
from main import hash_password
import secrets
import time

def register_student():
    init_db()
    email = "student@example.test"
    name = "Học viên"
    password = "Test-password-123"

    salt = secrets.token_hex(16)
    try:
        with database() as conn:
            conn.execute(
                "INSERT INTO users(name,email,password_hash,salt,role,created_at) VALUES(?,?,?,?,'student',?)",
                (name, email, hash_password(password, salt), salt, int(time.time()))
            )
        print(f"Created student: {email} / {password}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    register_student()
