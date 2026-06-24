#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")"

PY="${PYTHON:-python3.11}"
if ! command -v "$PY" >/dev/null 2>&1; then
  PY=python3.12
fi
if ! command -v "$PY" >/dev/null 2>&1; then
  PY=python3
fi

if [[ ! -d .build-venv ]]; then
  echo "→ Creating build virtualenv ($PY)..."
  "$PY" -m venv .build-venv
fi
# shellcheck disable=SC1091
source .build-venv/bin/activate

echo "→ Installing build dependencies..."
python -m pip install -q -r requirements-build.txt

echo "→ Cleaning previous build..."
rm -rf build dist

echo "→ Building VibeCode Translator.app (this may take a few minutes)..."
python setup.py py2app

echo ""
echo "✅ Done: dist/VibeCode Translator.app"
echo "   Open with: open \"dist/VibeCode Translator.app\""
