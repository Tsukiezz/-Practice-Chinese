import sys
sys.stdout.reconfigure(encoding='utf-8')
from database import database
import json

with database() as conn:
    rows = conn.execute('SELECT id, title, hsk, status, duration_minutes, questions_json FROM exams').fetchall()
    print(f"Total exams in DB: {len(rows)}")
    for r in rows:
        qs = json.loads(r['questions_json'])
        sections = set(q.get('section', '') for q in qs)
        print(f"ID: {r['id']}, HSK: {r['hsk']}, Title: {r['title']}, Status: {r['status']}, Qs: {len(qs)}, Sections: {sections}")
