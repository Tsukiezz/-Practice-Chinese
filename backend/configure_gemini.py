"""Enable the server-side Gemini grader without printing the API key."""
import sys

from database import database, init_db
from services import DEFAULT_GEMINI_MODEL, configured_api_key


def configure() -> None:
    if not configured_api_key():
        raise SystemExit("Chưa có GEMINI_API_KEY trong backend/.env")

    init_db()
    with database() as conn:
        conn.execute(
            """
            UPDATE ai_config
            SET model=?, enabled=1, temperature=0.1, max_tokens=1000,
                version=version+1
            WHERE id=1
              AND (model<>? OR enabled<>1 OR temperature<>0.1 OR max_tokens<>1000)
            """,
            (DEFAULT_GEMINI_MODEL, DEFAULT_GEMINI_MODEL),
        )

    print(f"Đã bật Gemini với model {DEFAULT_GEMINI_MODEL}. API key không được hiển thị.")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    configure()
