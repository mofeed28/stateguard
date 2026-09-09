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

base_url="${1:-${STATEGUARD_BASE_URL:-http://127.0.0.1:8787}}"
live_headers=()
if [[ -n "${STATEGUARD_LIVE_DEMO_KEY:-}" ]]; then
  live_headers=(-H "X-StateGuard-Live-Key: $STATEGUARD_LIVE_DEMO_KEY")
fi
curl -fsS "$base_url/api/health"
curl -fsS "$base_url/api/incidents/tradeops-ambiguous-cancel-double-entry/structured-output" >/dev/null
curl -fsS "$base_url/api/incidents/tradeops-ambiguous-cancel-double-entry/observability" >/dev/null
curl -fsS \
  -H "Content-Type: application/json" \
  "${live_headers[@]}" \
  -d '{
    "domain": "Invoice collection",
    "agent_belief": "Agent believes invoice #104 was paid and marks the account as settled.",
    "external_reality": "Bank API shows no settled payment and the invoice remains unpaid.",
    "risky_action": "Close the collection task and stop follow-up reminders."
  }' \
  "$base_url/api/simulate-mismatch" >/dev/null
if [[ -n "${STATEGUARD_LIVE_DEMO_KEY:-}" ]]; then
  curl -fsS \
    -H "Content-Type: application/json" \
    "${live_headers[@]}" \
    -d '{
      "domain": "Invoice collection",
      "agent_belief": "Agent believes invoice #104 was paid and marks the account as settled.",
      "external_reality": "Bank API shows no settled payment and the invoice remains unpaid.",
      "risky_action": "Close the collection task and stop follow-up reminders."
    }' \
    "$base_url/api/simulate-mismatch/live" >/dev/null
fi

echo
echo "StateGuard smoke checks passed for $base_url"
