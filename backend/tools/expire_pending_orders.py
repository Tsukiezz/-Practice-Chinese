"""Inspect stale orders; --apply reconciles each gateway order before local expiry.

No records are deleted and late authenticated payments remain recoverable.
Provider failures are reported and left pending by this maintenance command.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from dotenv import dotenv_values
from database import database
from sepay_gateway import reconcile_order, settings
import httpx


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    env = dotenv_values(ROOT / '.vercel/.env.production.local')
    for key in ('TURSO_DATABASE_URL', 'TURSO_AUTH_TOKEN'):
        value = env.get(key)
        if not value or value == '[SENSITIVE]':
            raise SystemExit('Missing production database configuration')
        os.environ[key] = value
    cutoff = int(time.time()) - 600
    with database() as conn:
        rows = conn.execute("SELECT order_code,user_id,status,payment_gateway,created_at FROM premium_orders WHERE status='pending' AND created_at<=? ORDER BY id", (cutoff,)).fetchall()
    print(json.dumps({'expired_pending_count': len(rows), 'apply': args.apply}))
    for row in rows:
        code = row['order_code']
        if not args.apply:
            print(json.dumps({'order_code': code, 'status': row['status'], 'created_at': row['created_at']}))
            continue
        if row['payment_gateway'] == 'sepay_pg':
            try:
                merchant, secret, _ = settings()
                response = httpx.get('https://pgapi.sepay.vn/v1/order/detail/' + code,
                                     auth=(merchant, secret), timeout=8, follow_redirects=False)
                response.raise_for_status()
                detail = response.json()['data']
                if detail.get('order_invoice_number') != code:
                    raise ValueError('Invoice mismatch')
                if detail.get('order_status') == 'CAPTURED':
                    reconcile_order(code, row['user_id'])
                    with database() as conn:
                        state = conn.execute('SELECT status FROM premium_orders WHERE order_code=?', (code,)).fetchone()['status']
                    print(json.dumps({'order_code': code, 'status': state, 'action': 'reconciled'}))
                    continue
            except Exception as error:
                print(json.dumps({'order_code': code, 'action': 'skipped', 'error_type': type(error).__name__}))
                continue
        with database() as conn:
            count = conn.execute("UPDATE premium_orders SET status='cancelled' WHERE order_code=? AND status='pending' AND created_at<=?", (code, cutoff)).rowcount
        print(json.dumps({'order_code': code, 'action': 'cancelled', 'changed': count}))


if __name__ == '__main__':
    main()
