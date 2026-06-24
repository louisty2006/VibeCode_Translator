#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

if [[ ! -d venv311 ]]; then
  echo "❌ venv311 not found. Run ./setup.sh first."
  exit 1
fi

# shellcheck disable=SC1091
source venv311/bin/activate
python main.py
