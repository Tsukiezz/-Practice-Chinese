# -*- coding: utf-8 -*-
"""Migrate the 6 comprehensive 40-question exams to local SQLite and Turso cloud database."""
import json
import os
import sys
import urllib.request
from pathlib import Path
from dotenv import dotenv_values

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))

from database import database
from comprehensive_hsk_data import COMPREHENSIVE_EXAMS_HSK1_6, init_comprehensive_exams

print("1. Migrating to local SQLite database...")
with database() as conn:
    init_comprehensive_exams(conn)
    rows = conn.execute("SELECT id, title, hsk, status, duration_minutes FROM exams WHERE title LIKE '%Toàn diện%'").fetchall()
    print(f"Local comprehensive exams: {len(rows)}")
    for r in rows:
        print(f"  [HSK {r['hsk']}] ID: {r['id']}, Title: {r['title']}, Duration: {r['duration_minutes']} min, Status: {r['status']}")

print("\n2. Migrating to Turso Cloud Database...")
secrets = dotenv_values(ROOT / '.vercel' / '.env.production.local')
db_url = secrets.get('TURSO_DATABASE_URL')
token = secrets.get('TURSO_AUTH_TOKEN')

if not db_url or not token:
    print("WARNING: Missing Turso credentials in .vercel/.env.production.local, skipping Turso push.")
    sys.exit(0)

# Build HTTPS pipeline endpoint
pipeline_url = db_url.replace("libsql://", "https://") + "/v2/pipeline"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

def turso_execute(sql, params=None):
    stmt = {"sql": sql}
    if params:
        args = []
        for p in params:
            if isinstance(p, int):
                args.append({"type": "integer", "value": str(p)})
            elif isinstance(p, float):
                args.append({"type": "float", "value": p})
            elif p is None:
                args.append({"type": "null"})
            else:
                args.append({"type": "text", "value": str(p)})
        stmt["args"] = args
    
    payload = {"requests": [{"type": "execute", "stmt": stmt}]}
    req = urllib.request.Request(pipeline_url, data=json.dumps(payload).encode('utf-8'), headers=headers)
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        result = data["results"][0]
        if result["type"] == "error":
            raise RuntimeError(f"Turso error: {result['error']}")
        return result["response"]["result"]

# Check existing exams in Turso
res = turso_execute("SELECT id, title, hsk, questions_json FROM exams WHERE title LIKE '%Toàn diện%'")
existing_rows = res.get("rows", [])
print(f"Turso existing comprehensive exams: {len(existing_rows)}")

for exam in COMPREHENSIVE_EXAMS_HSK1_6:
    check = turso_execute("SELECT id, duration_minutes FROM exams WHERE title = ?", [exam["title"]])
    rows = check.get("rows", [])
    q_json = json.dumps(exam["questions"], ensure_ascii=False)
    if not rows:
        print(f"  Inserting HSK {exam['hsk']} to Turso: {exam['title']} (40 questions)...")
        turso_execute(
            "INSERT INTO exams (title, hsk, status, duration_minutes, questions_json) VALUES (?, ?, 'published', ?, ?)",
            [exam["title"], exam["hsk"], exam["duration_minutes"], q_json]
        )
    else:
        exam_id = int(rows[0][0]["value"])
        print(f"  Updating HSK {exam['hsk']} (ID {exam_id}) in Turso: {exam['title']}...")
        turso_execute(
            "UPDATE exams SET status='published', duration_minutes=?, questions_json=? WHERE id=?",
            [exam["duration_minutes"], q_json, exam_id]
        )

# Verify count in Turso
res_final = turso_execute("SELECT id, title, hsk, status, duration_minutes FROM exams WHERE title LIKE '%Toàn diện%'")
print(f"\nFinal Turso comprehensive exams count: {len(res_final.get('rows', []))}")
for row in res_final.get("rows", []):
    eid = row[0]["value"]
    title = row[1]["value"]
    hsk = row[2]["value"]
    status = row[3]["value"]
    dur = row[4]["value"]
    print(f"  [HSK {hsk}] ID: {eid}, Title: {title}, Duration: {dur} min, Status: {status}")

print("\nMigration completed successfully on BOTH local and Turso databases!")
