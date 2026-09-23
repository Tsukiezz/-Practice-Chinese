"""Copy a consistent SQLite snapshot to an EMPTY Turso database.

Run from repository root with --source backend/hanzi_go.db and
--env-file .vercel/.env.production.local. Never overwrites an existing database.
"""
import argparse
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import dotenv_values


def migrate(source, env_file):
    secrets = dotenv_values(env_file)
    from cloud_database import connect
    remote = connect(str(secrets.get('TURSO_DATABASE_URL') or ''), str(secrets.get('TURSO_AUTH_TOKEN') or ''))
    try:
        if remote.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall():
            raise RuntimeError('Destination is not empty; refusing to overwrite it')
        with tempfile.TemporaryDirectory(prefix='hanzigo-migration-') as folder:
            snapshot = Path(folder) / 'snapshot.db'
            with closing(sqlite3.connect(f'{Path(source).resolve().as_uri()}?mode=ro', uri=True)) as original:
                with closing(sqlite3.connect(snapshot)) as target:
                    original.backup(target)
            import database
            # Provision only the snapshot, never the running local database.
            database.DB_PATH = snapshot
            os.environ.pop('TURSO_DATABASE_URL', None)
            os.environ.pop('HANZIGO_DB_DRIVER', None)
            database.init_db()
            from vocabulary_catalog import init_catalog, refresh_search
            from usecase_features import init_features
            from lesson_catalog import init_lessons
            init_features()
            init_lessons()
            with database.database() as conn:
                init_catalog(conn)
                refresh_search(conn)
                for table in ('sessions', 'recovery_codes', 'request_limits'):
                    conn.execute(f'DELETE FROM {table}')
            with closing(sqlite3.connect(snapshot)) as local:
                tables = [r[0] for r in local.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
                expected = {t: (local.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone() or [0])[0] for t in tables}
                script = '\n'.join(local.iterdump())
                print(f'Migrating {len(tables)} tables, {len(script.encode())} bytes; sessions excluded', flush=True)
                remote.execute('PRAGMA foreign_keys=OFF')
                # iterdump wraps all schema and rows in one transaction.
                remote.executescript(script)
                remote.execute('PRAGMA foreign_keys=ON')
                actual = {t: (remote.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone() or [0])[0] for t in tables}
                assert actual == expected, 'Cloud row counts differ from snapshot'
                assert not remote.execute('PRAGMA foreign_key_check').fetchall(), 'Foreign key check failed'
                print('Verified table counts:', actual)
    finally:
        remote.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--env-file', required=True, type=Path)
    args = parser.parse_args()
    migrate(args.source, args.env_file)
