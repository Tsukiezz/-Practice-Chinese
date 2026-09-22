"""Exercise the libSQL bridge used by Vercel without a cloud credential."""
from pathlib import Path
import sqlite3
import tempfile
import unittest

from cloud_database import connect


class CloudDatabaseTest(unittest.TestCase):
    def test_rows_constraints_and_rollback(self):
        try:
            import libsql  # noqa: F401
        except ImportError:
            self.skipTest("libsql is not installed")
        with tempfile.TemporaryDirectory() as folder:
            conn = connect(Path(folder) / 'bridge.db')
            try:
                conn.execute('CREATE TABLE words(id INTEGER PRIMARY KEY, text TEXT UNIQUE)')
                conn.execute('INSERT INTO words(text) VALUES(?)', ('你好',))
                conn.commit()
                cursor = conn.execute('SELECT id,text FROM words')
                row = cursor.fetchone()
                self.assertEqual(dict(row), {'id': 1, 'text': '你好'})
                self.assertEqual(row[1], '你好')
                self.assertIsNone(cursor.fetchone())
                self.assertEqual(cursor.fetchall(), [])
                del cursor  # Native cursors retain the Windows file handle.
                with self.assertRaises(sqlite3.IntegrityError):
                    conn.execute('INSERT INTO words(text) VALUES(?)', ('你好',))
                conn.rollback()
                conn.execute('INSERT INTO words(text) VALUES(?)', ('再见',))
                conn.rollback()
                self.assertEqual(conn.execute('SELECT COUNT(*) FROM words').fetchone()[0], 1)
            finally:
                conn.close()
