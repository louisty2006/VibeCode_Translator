#!/bin/bash
# One-time setup for running from source (方式 B)
set -euo pipefail
cd "$(dirname "$0")"

PY="${PYTHON:-python3}"
echo "→ Creating virtualenv..."
"$PY" -m venv venv

# shellcheck disable=SC1091
source venv/bin/activate

echo "→ Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo "   Start the app:  ./run.sh"
echo "   (or: source venv/bin/activate && python main.py)"
