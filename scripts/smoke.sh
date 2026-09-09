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
curl -fsS \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "Invoice collection",
    "agent_belief": "Agent believes invoice #104 was paid and marks the account as settled.",
    "external_reality": "Bank API shows no settled payment and the invoice remains unpaid.",
    "risky_action": "Close the collection task and stop follow-up reminders."
  }' \
  "$base_url/api/simulate-mismatch" >/dev/null
curl -fsS \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "Invoice collection",
    "agent_belief": "Agent believes invoice #104 was paid and marks the account as settled.",
    "external_reality": "Bank API shows no settled payment and the invoice remains unpaid.",
    "risky_action": "Close the collection task and stop follow-up reminders."
  }' \
  "$base_url/api/simulate-mismatch/live" >/dev/null

echo
echo "StateGuard smoke checks passed for $base_url"
