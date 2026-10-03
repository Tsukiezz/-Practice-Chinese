import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))

from dotenv import dotenv_values
from cloud_database import connect

secrets = dotenv_values(ROOT / '.vercel' / '.env.production.local')
db_url = secrets.get('TURSO_DATABASE_URL')
token = secrets.get('TURSO_AUTH_TOKEN')

if not db_url or not token:
    print("Missing TURSO credentials in .vercel/.env.production.local")
    sys.exit(1)

print("Connecting to Turso:", db_url)
conn = connect(db_url, auth_token=token)

print("Checking and applying columns to users table on Turso...")
user_cols = {row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()}
if 'premium_until' not in user_cols:
    conn.execute('ALTER TABLE users ADD COLUMN premium_until INTEGER NOT NULL DEFAULT 0')
    print("Added premium_until column to users table.")
if 'streak_freezes' not in user_cols:
    conn.execute('ALTER TABLE users ADD COLUMN streak_freezes INTEGER NOT NULL DEFAULT 0')
    print("Added streak_freezes column to users table.")

print("Creating sepay_config, premium_orders, and vouchers tables on Turso...")
conn.executescript("""
CREATE TABLE IF NOT EXISTS sepay_config (
    id INTEGER PRIMARY KEY CHECK(id=1),
    bank_name TEXT NOT NULL DEFAULT 'MBBank',
    bank_account TEXT NOT NULL DEFAULT '0399888999',
    account_holder TEXT NOT NULL DEFAULT 'NGUYEN VO VINH NIEN',
    merchant_id TEXT NOT NULL DEFAULT 'SP-LIVE-O573535',
    api_key TEXT NOT NULL DEFAULT 'spsk_live_paj8JXvTF1ouCh8HeE4mRevPMmX1Ei1o',
    is_active INTEGER NOT NULL DEFAULT 1,
    version INTEGER NOT NULL DEFAULT 1
);

INSERT OR IGNORE INTO sepay_config(id, bank_name, bank_account, account_holder, merchant_id, api_key, is_active)
VALUES(1, 'MBBank', '0399888999', 'NGUYEN VO VINH NIEN', 'SP-LIVE-O573535', 'spsk_live_paj8JXvTF1ouCh8HeE4mRevPMmX1Ei1o', 1);

UPDATE sepay_config
SET merchant_id = 'SP-LIVE-O573535',
    api_key = 'spsk_live_paj8JXvTF1ouCh8HeE4mRevPMmX1Ei1o',
    is_active = 1
WHERE id = 1;

CREATE TABLE IF NOT EXISTS premium_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_code TEXT NOT NULL UNIQUE,
    user_id INTEGER NOT NULL REFERENCES users(id),
    plan_type TEXT NOT NULL,
    amount INTEGER NOT NULL,
    original_amount INTEGER NOT NULL,
    voucher_code TEXT,
    discount_percent INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','completed','cancelled')),
    payment_gateway TEXT NOT NULL DEFAULT 'sepay',
    sepay_transaction_id TEXT,
    sepay_reference_code TEXT,
    created_at INTEGER NOT NULL,
    completed_at INTEGER
);
CREATE INDEX IF NOT EXISTS idx_premium_orders_code ON premium_orders(order_code);
CREATE INDEX IF NOT EXISTS idx_premium_orders_user ON premium_orders(user_id);

CREATE TABLE IF NOT EXISTS vouchers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    discount_percent INTEGER NOT NULL DEFAULT 0,
    is_free_month INTEGER NOT NULL DEFAULT 0,
    max_uses INTEGER NOT NULL DEFAULT 1,
    used_count INTEGER NOT NULL DEFAULT 0,
    created_by TEXT NOT NULL DEFAULT 'admin',
    user_id INTEGER,
    description TEXT NOT NULL DEFAULT '',
    is_active INTEGER NOT NULL DEFAULT 1,
    expires_at INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_vouchers_code ON vouchers(code);
CREATE INDEX IF NOT EXISTS idx_vouchers_active ON vouchers(is_active);
""")

print("Migration completed successfully on Turso!")
cfg = conn.execute("SELECT * FROM sepay_config WHERE id=1").fetchone()
print("Turso SePay config:", cfg)
