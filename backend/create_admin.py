"""Interactive, explicit administrator provisioning; no default password."""
import getpass
from pathlib import Path
import secrets
import sqlite3
import sys
import time

_backend_dir = Path(__file__).resolve().parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

try:
    from database import audit, database, init_db
    from main import hash_password
    from models import Register
except ImportError:
    from backend.database import audit, database, init_db  # type: ignore
    from backend.main import hash_password  # type: ignore
    from backend.models import Register  # type: ignore



def main():
    init_db()
    print("Tạo tài khoản quản trị HanziGo")
    body = Register(name=input("Tên: "), email=input("Email: "), password=getpass.getpass("Mật khẩu (ít nhất 8 ký tự): "))
    if body.password != getpass.getpass("Nhập lại mật khẩu: "):
        raise SystemExit("Mật khẩu xác nhận không khớp")
    salt = secrets.token_hex(16)
    try:
        with database() as conn:
            uid = conn.execute("INSERT INTO users(name,email,password_hash,salt,role,created_at) VALUES(?,?,?,?,'admin',?)",
                               (body.name, body.email, hash_password(body.password, salt), salt, int(time.time()))).lastrowid
            audit(conn, uid, "provision", "user", uid, None,
                  {"name": body.name, "email": body.email, "role": "admin"})
    except sqlite3.IntegrityError:
        raise SystemExit("Email đã tồn tại. Dùng trang Admin để đổi quyền; công cụ không ghi đè tài khoản.")
    print("Đã tạo tài khoản Admin. Mở http://127.0.0.1:8010/admin để đăng nhập.")


if __name__ == "__main__":
    import sys
    _reconfig = getattr(sys.stdout, "reconfigure", None)
    if callable(_reconfig):
        _reconfig(encoding="utf-8")
    main()
