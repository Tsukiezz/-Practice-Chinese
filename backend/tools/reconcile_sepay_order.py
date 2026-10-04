"""Inspect one existing production order; --apply verifies SePay before granting.

Database credentials come from the ignored Vercel env file. Gateway credentials
come from backend/.env or the process environment; secret values are never printed.
"""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from dotenv import dotenv_values
from database import database
from sepay_gateway import reconcile_order


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('order_code')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    env = dotenv_values(ROOT / '.vercel/.env.production.local')
    for key in ('TURSO_DATABASE_URL', 'TURSO_AUTH_TOKEN'):
        value = env.get(key)
        if not value or value == '[SENSITIVE]':
            raise SystemExit('Missing production database configuration')
        os.environ[key] = value
    with database() as conn:
        row = conn.execute('SELECT order_code,user_id,amount,plan_type,status FROM premium_orders WHERE order_code=?', (args.order_code,)).fetchone()
    if not row:
        raise SystemExit('Order not found')
    print(json.dumps(dict(row)))
    if args.apply:
        reconcile_order(row['order_code'], row['user_id'])
        with database() as conn:
            result = conn.execute('SELECT o.order_code,o.status,o.completed_at,u.premium_until FROM premium_orders o JOIN users u ON u.id=o.user_id WHERE o.order_code=?', (args.order_code,)).fetchone()
        print(json.dumps(dict(result)))
        if result['status'] != 'completed':
            raise SystemExit('Payment not verified; no manual grant performed')


if __name__ == '__main__':
    main()
