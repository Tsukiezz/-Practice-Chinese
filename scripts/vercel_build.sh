#!/usr/bin/env bash
set -euo pipefail
sdk_dir="/tmp/hanzigo-flutter-3.47.2"
if [ ! -x "$sdk_dir/bin/flutter" ]; then
  git clone --depth 1 --branch 3.47.2 https://github.com/flutter/flutter.git "$sdk_dir"
fi
export PATH="$sdk_dir/bin:$PATH"
flutter config --no-analytics
flutter pub get

mkdir -p public

echo "=== CHECKING FLUTTER CODE ANALYSIS ==="
flutter analyze > /tmp/analyze.log 2>&1 || true
cat /tmp/analyze.log

echo "=== COMPILING FLUTTER WEB ==="
if ! flutter build web --no-wasm-dry-run > /tmp/build.log 2>&1; then
  echo "FLUTTER BUILD FAILED!"
  cat /tmp/build.log

  python3 -c "
import sys, time
sys.path.insert(0, 'backend')
try:
    from database import database
    with database() as db:
        db.execute('CREATE TABLE IF NOT EXISTS _build_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT, created_at INTEGER)')
        with open('/tmp/analyze.log', 'r', errors='ignore') as f:
            an = f.read()
        with open('/tmp/build.log', 'r', errors='ignore') as f:
            bl = f.read()
        msg = '=== FLUTTER ANALYZE ===\n' + an + '\n\n=== FLUTTER BUILD ===\n' + bl
        db.execute('INSERT INTO _build_logs (message, created_at) VALUES (?, ?)', (msg, int(time.time())))
        print('Saved build log to Turso successfully!')
except Exception as e:
    print('Failed to write to Turso:', e)
" || true

  exit 1
fi

cp -R build/web/. public/
