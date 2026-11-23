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
flutter analyze --no-pub --no-fatal-infos

echo "=== COMPILING FLUTTER WEB ==="
flutter build web --no-pub --no-wasm-dry-run

cp -R build/web/. public/

# Ensure all logo paths exist and are accessible everywhere
mkdir -p public/assets/images public/assets/assets/images
cp -f assets/images/logo.png public/logo.png
cp -f assets/images/logo.png public/assets/images/logo.png
cp -f assets/images/logo.png public/assets/assets/images/logo.png

