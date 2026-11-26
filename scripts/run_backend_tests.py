"""Run backend tests on disposable local data, never the configured live database.

python scripts/run_backend_tests.py [test_assessment_integrity test_ai_exam ...]
Set HANZIGO_DB_DRIVER=libsql to exercise the local libSQL adapter as well.
"""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / 'backend'


def main():
    with tempfile.TemporaryDirectory(prefix='hanzigo-tests-') as temporary:
        os.environ['DATABASE_PATH'] = str(Path(temporary) / 'isolated.db')
        os.environ['TESTING'] = '1'
        os.environ['OTP_HASH_SECRET'] = 'isolated-test-otp-secret-not-for-production'
        os.environ.pop('VERCEL', None)
        # dotenv must not replace these with local production credentials.
        for key in ('TURSO_DATABASE_URL', 'TURSO_AUTH_TOKEN', 'GEMINI_API_KEY', 'AI_API_KEY',
                    'GEMINI_FALLBACK_API_KEYS', 'SMTP_HOST', 'SMTP_SERVER', 'SMTP_USERNAME',
                    'SMTP_USER', 'SMTP_PASSWORD', 'SMTP_PASS', 'SMTP_KEY', 'SMTP_FROM',
                    'SMTP_FROM_EMAIL', 'BREVO_SMTP_HOST', 'BREVO_SMTP_KEY', 'BREVO_API_KEY',
                    'SENDINBLUE_API_KEY', 'EMAIL_API_KEY', 'MAIL_HOST', 'MAIL_USERNAME',
                    'MAIL_PASSWORD', 'BREVO_USERNAME', 'BREVO_USER', 'EMAIL_FROM', 'MAIL_FROM'):
            os.environ[key] = ''
        sys.path.insert(0, str(BACKEND))
        if len(sys.argv) == 2 and sys.argv[1] in ('--smoke-browser', '--smoke-unified'):
            from importlib import import_module
            import_module(sys.argv[1][2:].replace('-', '_')).run()
            return 0
        print('Preparing isolated backend test database...', flush=True)
        from fastapi.testclient import TestClient
        from main import app
        from seed import seed
        from vocabulary_catalog import import_corpus
        with TestClient(app):
            seed()
            import_corpus()
        print('Running tests on disposable local data.', flush=True)
        names = sys.argv[1:]
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromNames(names) if names else loader.discover(str(BACKEND), pattern='test_*.py')
        # Individual delivery tests can override this patch with their own mock.
        with patch('main.send_verification_email', return_value=True):
            result = unittest.TextTestRunner(verbosity=2).run(suite)
        return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
