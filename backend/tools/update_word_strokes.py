# -*- coding: utf-8 -*-
"""Update standard strokes for '你好' and '学习' in local SQLite and Turso Cloud."""
import json
import os
import sys
import urllib.request
from pathlib import Path
from dotenv import dotenv_values

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')  # type: ignore

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))

def stroke(*points):
    return [{"x": x, "y": y} for x, y in points]

# Standard 13 strokes for "你好" (你: 7 nét bên trái + 好: 6 nét bên phải)
NI_HAO_STROKES = [
    # --- Chữ 你 (7 nét) ---
    # 1. 撇 (bên trái)
    stroke((180, 180), (110, 420)),
    # 2. 竖 (thân người đứng)
    stroke((155, 360), (155, 850)),
    # 3. 撇 (đầu bên phải)
    stroke((280, 180), (225, 340)),
    # 4. 横撇
    stroke((250, 330), (415, 330), (370, 440)),
    # 5. 竖钩
    stroke((325, 380), (325, 820), (275, 860)),
    # 6. 撇 (dưới)
    stroke((270, 530), (210, 720)),
    # 7. 点 (dưới)
    stroke((375, 530), (430, 720)),

    # --- Chữ 好 (6 nét) ---
    # 8. 撇点 (bộ Nữ)
    stroke((670, 210), (620, 560), (745, 740)),
    # 9. 撇 (bộ Nữ)
    stroke((730, 340), (670, 640), (580, 800)),
    # 10. 提 (bộ Nữ)
    stroke((570, 510), (760, 510)),
    # 11. 横撇 (bộ Tử)
    stroke((790, 270), (920, 270), (840, 430)),
    # 12. 弯钩 (bộ Tử)
    stroke((860, 420), (860, 790), (810, 850)),
    # 13. 横 (bộ Tử)
    stroke((740, 560), (950, 560)),
]

# Standard 11 strokes for "学习" (学: 8 nét bên trái + 习: 3 nét bên phải)
XUE_XI_STROKES = [
    # --- Chữ 学 (8 nét) ---
    # 1. 点
    stroke((220, 160), (250, 240)),
    # 2. 点
    stroke((310, 150), (310, 230)),
    # 3. 撇
    stroke((400, 160), (360, 250)),
    # 4. 点 (bộ Mịch)
    stroke((160, 340), (190, 420)),
    # 5. 横撇/横钩 (bộ Mịch)
    stroke((170, 350), (440, 350), (400, 440)),
    # 6. 横撇/弯钩 (bộ Tử)
    stroke((240, 490), (370, 490), (260, 620), (360, 620)),
    # 7. 竖钩 (bộ Tử)
    stroke((310, 490), (310, 860), (260, 820)),
    # 8. 横 (bộ Tử)
    stroke((140, 670), (460, 670)),

    # --- Chữ 习 (3 nét) ---
    # 9. 横折钩
    stroke((600, 310), (900, 310), (900, 780), (830, 840)),
    # 10. 点
    stroke((710, 440), (780, 530)),
    # 11. 提
    stroke((620, 750), (800, 660)),
]

print(f"Total strokes for 你好: {len(NI_HAO_STROKES)} nét")
print(f"Total strokes for 学习: {len(XUE_XI_STROKES)} nét")

# 1. Update SQLite local
from database import database
with database() as conn:
    conn.execute(
        "UPDATE vocabulary SET strokes_json = ?, version = version + 1 WHERE hanzi = ?",
        (json.dumps(NI_HAO_STROKES, ensure_ascii=False), "你好")
    )
    conn.execute(
        "UPDATE vocabulary SET strokes_json = ?, version = version + 1 WHERE hanzi = ?",
        (json.dumps(XUE_XI_STROKES, ensure_ascii=False), "学习")
    )
    rows = conn.execute("SELECT id, hanzi, json_array_length(strokes_json) as cnt FROM vocabulary WHERE hanzi IN ('你好', '学习')").fetchall()
    print("Local SQLite updated:")
    for r in rows:
        print(f"  ID {r['id']}: {r['hanzi']} -> {r['cnt']} nét")

# 2. Update Turso Cloud Database
secrets = dotenv_values(ROOT / '.vercel' / '.env.production.local')
db_url = secrets.get('TURSO_DATABASE_URL')
token = secrets.get('TURSO_AUTH_TOKEN')

if db_url and token:
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
            return json.loads(resp.read().decode('utf-8'))

    print("\nUpdating Turso Cloud...")
    turso_execute(
        "UPDATE vocabulary SET strokes_json = ?, version = version + 1 WHERE hanzi = ?",
        [json.dumps(NI_HAO_STROKES, ensure_ascii=False), "你好"]
    )
    turso_execute(
        "UPDATE vocabulary SET strokes_json = ?, version = version + 1 WHERE hanzi = ?",
        [json.dumps(XUE_XI_STROKES, ensure_ascii=False), "学习"]
    )
    res = turso_execute("SELECT id, hanzi, json_array_length(strokes_json) FROM vocabulary WHERE hanzi IN ('你好', '学习')")
    cols = [c["name"] for c in res["results"][0]["response"]["result"]["cols"]]
    rows = res["results"][0]["response"]["result"]["rows"]
    print("Turso Cloud verified:")
    for row in rows:
        print(f"  {row[1]['value']} -> {row[2]['value']} nét")
else:
    print("Turso credentials not found, skipping cloud update.")
