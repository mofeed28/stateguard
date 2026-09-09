#!/usr/bin/env bash
set -euo pipefail

if [[ -n "${PYTHON_BIN:-}" ]]; then
  python_bin="$PYTHON_BIN"
elif [[ -x ".venv/bin/python" ]]; then
  python_bin=".venv/bin/python"
else
  python_bin="python3"
fi
"$python_bin" -m pytest -q

base_url="${STATEGUARD_BASE_URL:-http://127.0.0.1:8787}"
curl -fsS "$base_url/api/health"
curl -fsS "$base_url/api/incidents/tradeops-ambiguous-cancel-double-entry/structured-output" >/dev/null
curl -fsS "$base_url/api/incidents/tradeops-ambiguous-cancel-double-entry/observability" >/dev/null

echo
echo "StateGuard smoke checks passed for $base_url"
