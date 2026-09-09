#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

. .venv/bin/activate
python -m pip install -e ".[dev]"
uvicorn stateguard.app:app --app-dir backend --host 127.0.0.1 --port "${PORT:-8787}"

