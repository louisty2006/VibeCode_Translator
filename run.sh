#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

if [[ ! -d venv ]]; then
  echo "❌ venv not found. Run ./setup.sh first."
  exit 1
fi

# shellcheck disable=SC1091
source venv/bin/activate
python main.py
