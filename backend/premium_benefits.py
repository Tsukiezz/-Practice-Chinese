"""Server-owned entitlements and idempotent monthly streak protection (UTC+7)."""
from datetime import datetime, timedelta, timezone
import time

from fastapi import Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from typing import Literal
from database import database

LOCAL_TZ = timezone(timedelta(hours=7))


def premium(user, now=None):
    return int(user.get('premium_until') or 0) > (int(time.time()) if now is None else now)


def init_benefits(conn):
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS learner_benefits (
            user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            brush TEXT NOT NULL DEFAULT 'default',
            palette TEXT NOT NULL DEFAULT 'dark',
            protection_since TEXT NOT NULL DEFAULT '',
            known_until INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS streak_protection (
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            day TEXT NOT NULL,
            PRIMARY KEY(user_id,day)
        );
        CREATE TABLE IF NOT EXISTS learner_activity_days (
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            day TEXT NOT NULL, PRIMARY KEY(user_id,day)
        );
    ''')


def benefits(conn, user, now=None):
    now = int(time.time()) if now is None else now
    today = datetime.fromtimestamp(now, LOCAL_TZ).date().isoformat()
    active = premium(user, now)
    conn.execute('INSERT OR IGNORE INTO learner_benefits(user_id) VALUES(?)', (user['id'],))
    row = dict(conn.execute('SELECT * FROM learner_benefits WHERE user_id=?', (user['id'],)).fetchone())
    if active and (not row['protection_since'] or (row['known_until'] <= now and row['known_until'] != user['premium_until'])):
        conn.execute('UPDATE learner_benefits SET protection_since=? WHERE user_id=?', (today, user['id']))
        row['protection_since'] = today
    elif not active and row['protection_since']:
        conn.execute("UPDATE learner_benefits SET protection_since='' WHERE user_id=?", (user['id'],))
        row['protection_since'] = ''
    conn.execute('UPDATE learner_benefits SET known_until=? WHERE user_id=?', (user.get('premium_until', 0), user['id']))
    used = conn.execute('SELECT COUNT(*) FROM streak_protection WHERE user_id=? AND day LIKE ?',
                        (user['id'], today[:7] + '%')).fetchone()[0]
    return {'is_premium': active, 'premium_until': user.get('premium_until', 0),
            'ai_daily_limit': None if active else 3, 'max_hsk': 9 if active else 6,
            'brush': row['brush'] if active else 'default',
            'palette': row['palette'] if active else 'dark',
            'streak_freezes': max(0, 3 - used) if active else 0,
            'freeze_month': today[:7], 'protection_since': row['protection_since'],
            'gold_badge': active}


def protected_streak(conn, user, activity_days, now=None):
    now = int(time.time()) if now is None else now
    today = datetime.fromtimestamp(now, LOCAL_TZ).date()
    state = benefits(conn, user, now)
    days = set(activity_days)
    protected = {r[0] for r in conn.execute('SELECT day FROM streak_protection WHERE user_id=?', (user['id'],))}
    # Protect only an existing chain, never invent learning or consume today's credit.
    past = sorted(d for d in days | protected if d < today.isoformat())
    if state['is_premium'] and past:
        right = today
        for left_key in reversed(past):
            left = datetime.fromisoformat(left_key).date()
            gap = (right - left).days - 1
            if gap > 6:  # Even across a month boundary only 3+3 credits are possible.
                break
            missing = [(left + timedelta(days=i)).isoformat() for i in range(1, gap + 1)]
            if missing and missing[0] < state['protection_since']:
                break
            counts = {}
            for key in protected | set(missing):
                counts[key[:7]] = counts.get(key[:7], 0) + 1
            if any(n > 3 for n in counts.values()):
                break
            for key in missing:
                conn.execute('INSERT OR IGNORE INTO streak_protection(user_id,day) VALUES(?,?)', (user['id'], key))
            protected.update(missing)
            right = left
    chain = days | protected
    cursor = today if today.isoformat() in days else today - timedelta(days=1)
    streak = 0
    while cursor.isoformat() in chain:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def streak_details(conn, user, activity_days, now=None):
    """Personal calendar; freeze days sustain a chain but never count as learning."""
    now = int(time.time()) if now is None else now
    today = datetime.fromtimestamp(now, LOCAL_TZ).date()
    days = {d for d in activity_days if d and d <= today.isoformat()}
    current = protected_streak(conn, user, days, now)
    protected = {r[0] for r in conn.execute(
        'SELECT day FROM streak_protection WHERE user_id=?', (user['id'],)) if r[0] <= today.isoformat()}
    longest = run = 0
    previous = None
    for key in sorted(days | protected):
        day = datetime.fromisoformat(key).date()
        run = run + 1 if previous and day == previous + timedelta(days=1) else 1
        longest = max(longest, run)
        previous = day
    state = benefits(conn, user, now)
    calendar = []
    for offset in range(27, -1, -1):
        key = (today - timedelta(days=offset)).isoformat()
        calendar.append({'date': key, 'status': 'learned' if key in days else 'protected' if key in protected else 'empty'})
    return {'current': current, 'longest': longest, 'total_learning_days': len(days),
            'today': today.isoformat(), 'timezone': 'Asia/Ho_Chi_Minh',
            'learned_today': today.isoformat() in days, 'calendar': calendar,
            'is_premium': state['is_premium'], 'freezes_remaining': state['streak_freezes'],
            'freeze_month': state['freeze_month'],
            'next_milestone': next((n for n in (3, 7, 14, 30, 60, 100, 180, 365) if n > current), (current // 365 + 1) * 365)}


def record_learning(conn, user_id):
    conn.execute('INSERT OR IGNORE INTO learner_activity_days(user_id,day) VALUES(?,?)',
                 (user_id, datetime.now(LOCAL_TZ).date().isoformat()))


class Preferences(BaseModel):
    model_config = ConfigDict(extra='forbid')
    brush: Literal['default', 'brush', 'ink', 'calligraphy', 'pencil', 'marker', 'feather'] = 'default'
    palette: Literal['dark', 'purple', 'red', 'blue', 'yellow', 'orange', 'pink', 'pastelRed', 'pastelGreen'] = 'dark'


def register_benefits(app, current_user):
    @app.get('/api/me/benefits')
    def get_benefits(user=Depends(current_user)):
        with database() as conn:
            return benefits(conn, user)

    @app.put('/api/me/benefits/preferences')
    def set_preferences(body: Preferences, user=Depends(current_user)):
        with database() as conn:
            state = benefits(conn, user)
            if not state['is_premium'] and (body.brush != 'default' or body.palette != 'dark'):
                raise HTTPException(403, 'Tùy chọn này dành cho HanziGo Premium.')
            conn.execute('UPDATE learner_benefits SET brush=?,palette=? WHERE user_id=?',
                         (body.brush, body.palette, user['id']))
            return benefits(conn, user)
