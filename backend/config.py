"""Load backend-only environment variables from ``backend/.env``."""
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parent


def load_environment() -> None:
    """Load local secrets without overriding variables set by the host."""
    load_dotenv(BACKEND_DIR / ".env", override=False)


load_environment()
