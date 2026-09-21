"""Vercel ASGI entrypoint. Database credentials exist only in server env."""
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
if not os.getenv('TURSO_DATABASE_URL') or not os.getenv('TURSO_AUTH_TOKEN'):
    raise RuntimeError('Configure the persistent Turso database before deploying HanziGo')
os.environ['WEB_APP_DIR'] = str(ROOT / 'public')

from main import app  # noqa: E402,F401
