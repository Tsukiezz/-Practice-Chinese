"""Corpus coverage and mobile catalog tests on isolated databases."""
import json
from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

import database as storage
from main import app
from vocabulary_catalog import DATA, import_corpus, load_corpus


class VocabularyCatalogTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old = storage.DB_PATH
        storage.DB_PATH = Path(self.temp.name) / 'catalog.db'
        self.client = TestClient(app)
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        storage.DB_PATH = self.old
        self.temp.cleanup()

    def test_complete_source_and_localization(self):
        words = load_corpus()
        self.assertEqual(len(words), 4993)
        self.assertEqual(sum(map(len, words.values())), 5000)
        source = json.loads((DATA / 'hsk20_source.json').read_text(encoding='utf-8'))
        self.assertEqual([sum(r['hsk'] == hsk for r in source) for hsk in range(1, 7)],
                         [150, 150, 299, 601, 1300, 2500])
        self.assertEqual({s['pinyin'] for s in words['长']}, {'cháng', 'zhǎng'})
        for senses in words.values():
            for sense in senses:
                self.assertTrue(sense['meaning'].strip())
                self.assertTrue(sense['topic'])

    def test_import_preserves_existing_content_and_is_repeatable(self):
        with storage.database() as conn:
            word_id = conn.execute("INSERT INTO vocabulary(hanzi,pinyin,meaning,hsk,example,audio_url,strokes_json) VALUES(?,?,?,?,?,?,?)",
                                   ('一', 'yī', 'Nghĩa do Admin sửa', 1, 'Ví dụ riêng', '/media/kept.mp3', '[[{"x":1,"y":2}]]')).lastrowid
            before = dict(conn.execute('SELECT * FROM vocabulary WHERE id=?', (word_id,)).fetchone())
        first = import_corpus()
        second = import_corpus()
        self.assertEqual(first['inserted'], 4992)
        self.assertEqual(second['inserted'], 0)
        with storage.database() as conn:
            after = dict(conn.execute('SELECT * FROM vocabulary WHERE id=?', (word_id,)).fetchone())
            self.assertEqual(after, before)
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM vocabulary_catalog').fetchone()[0], 4993)
            self.assertEqual(conn.execute('PRAGMA foreign_key_check').fetchall(), [])

    def test_filters_search_pagination_and_polyphonic_senses(self):
        import_corpus()
        first = self.client.get('/api/vocabulary/page').json()
        self.assertEqual(first['total'], 4993)
        self.assertEqual(len(first['items']), 40)
        second = self.client.get('/api/vocabulary/page?offset=40').json()
        self.assertFalse({r['id'] for r in first['items']} & {r['id'] for r in second['items']})
        apple = self.client.get('/api/vocabulary/page', params={'search': 'pingguo'}).json()
        self.assertIn('苹果', [r['hanzi'] for r in apple['items']])
        food = self.client.get('/api/vocabulary/page', params={'hsk': 1, 'topic': 'food', 'limit': 100}).json()
        self.assertGreater(food['total'], 0)
        self.assertTrue(all(r['hsk'] == 1 and 'food' in r['topics'] for r in food['items']))
        matches = self.client.get('/api/vocabulary/page', params={'search': '长', 'hsk': 2}).json()
        long_word = next(r for r in matches['items'] if r['hanzi'] == '长')
        self.assertEqual(len(long_word['senses']), 2)
        for params in ({'limit': 101}, {'hsk': 7}, {'offset': -1}):
            self.assertEqual(self.client.get('/api/vocabulary/page', params=params).status_code, 422)
        self.assertEqual(self.client.get('/api/vocabulary/page', params={'topic': 'unknown'}).json()['total'], 0)
        self.assertEqual(self.client.get('/api/vocabulary/page', params={'search': '%'}).json()['total'], 0)
        self.assertEqual(self.client.get('/api/vocabulary/page', params={'search': 'khong-co-tu-nay-123'}).json()['items'], [])


if __name__ == '__main__':
    unittest.main()
