"""Versioned HSK 2.0 corpus, topic facets and bounded mobile browsing."""
from collections import defaultdict
import json
from pathlib import Path
import sqlite3
import unicodedata

from typing import Any

from fastapi import APIRouter, Query

from database import database, init_db, DB_PATH, row_to_dict

DATA = Path(__file__).with_name('data')
router = APIRouter()


def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text.lower().replace('đ', 'd'))
                   if not unicodedata.combining(c))


def init_catalog(conn):
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS vocabulary_search (
            word_id INTEGER PRIMARY KEY REFERENCES vocabulary(id) ON DELETE CASCADE,
            search_text TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS vocabulary_catalog (
            word_id INTEGER PRIMARY KEY REFERENCES vocabulary(id) ON DELETE CASCADE,
            edition TEXT NOT NULL, hsk INTEGER NOT NULL CHECK(hsk BETWEEN 1 AND 6),
            senses_json TEXT NOT NULL, search_text TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS vocabulary_topics (
            word_id INTEGER NOT NULL REFERENCES vocabulary(id) ON DELETE CASCADE,
            topic TEXT NOT NULL, PRIMARY KEY(word_id,topic)
        );
        CREATE INDEX IF NOT EXISTS vocabulary_topics_topic ON vocabulary_topics(topic,word_id);
        CREATE INDEX IF NOT EXISTS vocabulary_catalog_hsk ON vocabulary_catalog(hsk,word_id);
    ''')



def refresh_search(conn, word_id=None):
    if word_id is None:
        rows = conn.execute('SELECT v.id,v.hanzi,v.pinyin,v.meaning FROM vocabulary v LEFT JOIN vocabulary_search s ON s.word_id=v.id WHERE s.word_id IS NULL').fetchall()
    else:
        rows = conn.execute('SELECT id,hanzi,pinyin,meaning FROM vocabulary WHERE id=?', (word_id,)).fetchall()
    conn.executemany('INSERT INTO vocabulary_search(word_id,search_text) VALUES(?,?) ON CONFLICT(word_id) DO UPDATE SET search_text=excluded.search_text',
        [(r['id'], normalize(' '.join([r['hanzi'], r['pinyin'], r['pinyin'].replace(' ', ''), r['meaning']]))) for r in rows])


def load_corpus():
    source = json.loads((DATA / 'hsk20_source.json').read_text(encoding='utf-8'))
    translated = json.loads((DATA / 'hsk20_vi.json').read_text(encoding='utf-8'))
    topics = json.loads((DATA / 'topics.json').read_text(encoding='utf-8'))
    by_id = {r['source_id']: r for r in translated}
    if len(source) != 5000 or len(by_id) != 5000 or len(translated) != 5000:
        raise ValueError('Expected exactly 5000 source entries and translations')
    if {r['source_id'] for r in source} != set(by_id):
        raise ValueError('Source and translation IDs do not match')
    words = defaultdict(list)
    for entry in source:
        local = by_id[entry['source_id']]
        if not local['meaning'].strip() or local['topic'] not in topics:
            raise ValueError('Missing meaning or invalid topic')
        words[entry['hanzi']].append({**entry, **local})
    if len(words) != 4993:
        raise ValueError('Unexpected unique headword coverage')
    return words


def import_corpus():
    # Validate everything before starting a write transaction.
    words = load_corpus()
    init_db()
    inserted = 0
    with database() as conn:
        init_catalog(conn)
        conn.execute('BEGIN IMMEDIATE')
        for hanzi, senses in words.items():
            pinyin = ' / '.join(dict.fromkeys(r['pinyin'] for r in senses))
            meaning = '; '.join(dict.fromkeys(r['meaning'] for r in senses))
            hsk = min(r['hsk'] for r in senses)
            existing = conn.execute('SELECT * FROM vocabulary WHERE hanzi=?', (hanzi,)).fetchone()
            if existing:
                word_id = existing['id']
            else:
                word_id = conn.execute(
                    'INSERT INTO vocabulary(hanzi,pinyin,meaning,hsk) VALUES(?,?,?,?)',
                    (hanzi, pinyin, meaning, hsk)).lastrowid
                inserted += 1
            # Preserve existing IDs, Admin content, recordings, stroke paths and linked history.
            compact = [{k: r[k] for k in ('source_id', 'pinyin', 'meaning', 'topic')} for r in senses]
            search = normalize(' '.join([hanzi, pinyin, pinyin.replace(' ', ''), meaning]))
            conn.execute('''INSERT INTO vocabulary_catalog VALUES(?,?,?,?,?)
                ON CONFLICT(word_id) DO UPDATE SET edition=excluded.edition,hsk=excluded.hsk,
                senses_json=excluded.senses_json,search_text=excluded.search_text''',
                (word_id, 'HSK 2.0', hsk, json.dumps(compact, ensure_ascii=False), search))
            conn.execute('DELETE FROM vocabulary_topics WHERE word_id=?', (word_id,))
            conn.executemany('INSERT INTO vocabulary_topics VALUES(?,?)',
                             [(word_id, topic) for topic in sorted({r['topic'] for r in senses})])
        refresh_search(conn)
    return {'inserted': inserted, 'headwords': len(words), 'source_entries': 5000}


@router.get('/api/vocabulary/page')
def vocabulary_page(search: str = Query('', max_length=120),
                    hsk: int | None = Query(None, ge=1, le=6),
                    topic: str | None = Query(None, max_length=40),
                    limit: int = Query(40, ge=1, le=100), offset: int = Query(0, ge=0)):
    labels = json.loads((DATA / 'topics.json').read_text(encoding='utf-8'))
    # Escape wildcard characters so searching '%' doesn't fetch the whole dictionary.
    needle = '%' + normalize(search.strip()).replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
    conditions = ["(s.search_text LIKE ? ESCAPE '\\' OR c.search_text LIKE ? ESCAPE '\\')"]
    params: list[Any] = [needle, needle]
    if not search.strip():
        conditions, params = ['1=1'], []
    if hsk:
        conditions.append('COALESCE(c.hsk,v.hsk)=?')
        params.append(hsk)
    base = ' FROM vocabulary v LEFT JOIN vocabulary_catalog c ON c.word_id=v.id LEFT JOIN vocabulary_search s ON s.word_id=v.id WHERE ' + ' AND '.join(conditions)
    with database() as conn:
        facets = conn.execute('SELECT t.topic,COUNT(*) AS count' + base.replace(' WHERE ', ' JOIN vocabulary_topics t ON t.word_id=v.id WHERE ') + ' GROUP BY t.topic', params).fetchall()
        if topic:
            base += ' AND EXISTS(SELECT 1 FROM vocabulary_topics t WHERE t.word_id=v.id AND t.topic=?)'
            params.append(topic)
        total_row = conn.execute('SELECT COUNT(*)' + base, params).fetchone()
        total = total_row[0] if total_row else 0
        rows = conn.execute('SELECT v.*,c.hsk AS catalog_hsk,c.senses_json' + base +
                            ' ORDER BY COALESCE(c.hsk,v.hsk),v.id LIMIT ? OFFSET ?', [*params, limit, offset]).fetchall()
        items = []
        for row in rows:
            item = row_to_dict(row)
            item['hsk'] = item.pop('catalog_hsk') or item['hsk']
            item['senses'] = json.loads(item.pop('senses_json') or '[]')
            item['strokes'] = json.loads(item.pop('strokes_json'))
            item['topics'] = sorted({s['topic'] for s in item['senses']})
            items.append(item)
    return {'items': items, 'total': total, 'offset': offset, 'limit': limit,
            'edition': 'HSK 2.0',
            'topics': [{'id': key, 'label': label, 'count': next((r['count'] for r in facets if r['topic'] == key), 0)} for key, label in labels.items()]}


if __name__ == '__main__':
    # Back up local data with SQLite's backup API before importing.
    if DB_PATH.exists():
        backup = DB_PATH.with_name(DB_PATH.stem + '.before-hsk20.db')
        if not backup.exists():
            with sqlite3.connect(DB_PATH) as src, sqlite3.connect(backup) as dst:
                src.backup(dst)
    print(json.dumps(import_corpus()))
