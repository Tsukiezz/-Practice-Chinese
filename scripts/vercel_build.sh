#!/usr/bin/env bash
set -euo pipefail
sdk_dir="/tmp/hanzigo-flutter-3.47.2"
if [ ! -x "$sdk_dir/bin/flutter" ]; then
  git clone --depth 1 --branch 3.47.2 https://github.com/flutter/flutter.git "$sdk_dir"
fi
export PATH="$sdk_dir/bin:$PATH"
flutter config --no-analytics
flutter pub get
echo "=== CHECKING FLUTTER CODE ANALYSIS ==="
flutter analyze || true
echo "=== COMPILING FLUTTER WEB ==="
flutter build web --no-wasm-dry-run
mkdir -p public
cp -R build/web/. public/

