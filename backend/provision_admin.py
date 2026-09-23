"""Provision and verify admin accounts for HanziGo."""
import os
import sys
from database import database, ensure_default_admin, init_db

_reconfig = getattr(sys.stdout, "reconfigure", None)
if callable(_reconfig):
    _reconfig(encoding="utf-8")


def main():
    init_db()
    with database() as conn:
        ensure_default_admin(conn)
        rows = conn.execute("SELECT id, name, email, role, is_active FROM users WHERE role='admin'").fetchall()
        print("=== CÁC TÀI KHOẢN ADMIN HIỆN TẠI TRONG HỆ THỐNG ===")
        for r in rows:
            print(f"- ID {r['id']}: {r['name']} <{r['email']}> | Role: {r['role']} | Active: {r['is_active']}")
        print("\nThông tin đăng nhập mặc định:")
        print("  Email: admin@hanzigo.com (hoặc nguyen.demo@example.test)")
        print("  Mật khẩu: Admin@HanziGo2026!")


if __name__ == "__main__":
    main()
