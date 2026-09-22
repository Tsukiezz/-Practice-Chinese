"""Clean up all non-admin / student accounts, keeping only admin accounts."""
import sys
from database import database, init_db


def clean_accounts():
    init_db()
    with database() as conn:
        # Get all non-admin users
        non_admins = conn.execute(
            "SELECT id, name, email, role FROM users WHERE role != 'admin'"
        ).fetchall()
        
        admin_users = conn.execute(
            "SELECT id, name, email, role FROM users WHERE role = 'admin'"
        ).fetchall()

        print(f"--- DANH SÁCH ADMIN ĐƯỢC GIỮ LẠI ({len(admin_users)} tài khoản) ---")
        for admin in admin_users:
            print(f"  ID {admin['id']}: {admin['name']} <{admin['email']}> (Role: {admin['role']})")

        print(f"\n--- TIẾN HÀNH XÓA {len(non_admins)} TÀI KHOẢN KHÔNG PHẢI ADMIN ---")
        non_admin_ids = [u["id"] for u in non_admins]
        non_admin_emails = [u["email"].lower() for u in non_admins]

        if non_admin_ids:
            placeholders = ",".join("?" * len(non_admin_ids))
            
            # Delete dependent records
            conn.execute(f"DELETE FROM sessions WHERE user_id IN ({placeholders})", non_admin_ids)
            conn.execute(f"DELETE FROM dictionary_history WHERE user_id IN ({placeholders})", non_admin_ids)
            conn.execute(f"DELETE FROM review_progress WHERE user_id IN ({placeholders})", non_admin_ids)
            conn.execute(f"DELETE FROM review_attempts WHERE user_id IN ({placeholders})", non_admin_ids)
            conn.execute(f"DELETE FROM capability_reports WHERE user_id IN ({placeholders})", non_admin_ids)
            conn.execute(f"DELETE FROM saved_words WHERE user_id IN ({placeholders})", non_admin_ids)
            conn.execute(f"DELETE FROM appeals WHERE user_id IN ({placeholders})", non_admin_ids)
            conn.execute(f"DELETE FROM results WHERE user_id IN ({placeholders})", non_admin_ids)
            conn.execute(f"DELETE FROM ai_usage WHERE user_id IN ({placeholders})", non_admin_ids)
            conn.execute(f"DELETE FROM audit_logs WHERE actor_id IN ({placeholders})", non_admin_ids)
            
            email_placeholders = ",".join("?" * len(non_admin_emails))
            conn.execute(f"DELETE FROM verification_codes WHERE email IN ({email_placeholders})", non_admin_emails)

            # Delete users
            deleted = conn.execute(f"DELETE FROM users WHERE id IN ({placeholders})", non_admin_ids).rowcount
            print(f"Đã xóa thành công {deleted} tài khoản học viên và dữ liệu liên quan.")
        else:
            print("Không có tài khoản học viên nào cần xóa.")

        # Final verification
        remaining = conn.execute("SELECT id, name, email, role FROM users").fetchall()
        print(f"\n--- TỔNG KẾT TÀI KHOẢN CÒN LẠI TRONG CƠ SỞ DỮ LIỆU ({len(remaining)}) ---")
        for user in remaining:
            print(f"  ID {user['id']}: {user['name']} <{user['email']}> (Role: {user['role']})")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    clean_accounts()
