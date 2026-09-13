# StateGuard submission packet

## Title and track

StateGuard — check reality before retrying.

Professional Agents.

## Problem and audience

Small teams rely on automated client communication but still need to investigate ambiguous provider failures. An email API can time out after accepting a message. If the worker trusts its local failure flag, a retry can deliver the message twice.

## What we built

StateGuard implements an email retry workflow with a transactional action gate, persistent run state, versioned human approval, and a delivery ledger. The current provider is a stateful sandbox: no real email is sent.

Healthy work completes without human intervention. Pending or unavailable evidence holds the retry. When confirmed provider delivery contradicts the worker's belief, the gate stops the duplicate and asks the owner to reconcile. Approval updates local state only after rechecking the current evidence. The resulting delivery is verified and recorded. Concurrent worker calls and repeated approvals do not create additional deliveries.

A separate background worker can process new work and refresh uncertain runs. The dashboard displays the audit trail and polls for meaningful state changes.

## Use of Strands

A live Strands agent on Bedrock investigates through two tools: inspect_worker_history and query_delivery_provider. Both must execute before the structured diagnosis is accepted. The dashboard shows actual tool results and measured runtime. Agent analysis explains the incident; deterministic code enforces the action gate. Failed model calls remain explicit failures.

The implementation includes the live invocation, but a real Bedrock run must be verified before claiming a successful live demo. Archived multi-role replays are clearly labeled scripted illustrations.

## Evidence

The repository contains tests for duplicate prevention, concurrent retries, stale approval, unknown runs, healthy completion, uncertain evidence, background processing, and redaction. A four-scenario evaluation is reproducible using python scripts/evaluate.py. The comparison baseline retries from local belief without checking provider state. This small constructed evaluation is not a real-world effectiveness or LLM-accuracy benchmark.

## Architecture and limitations

FastAPI, SQLite, a standalone worker, Strands Agents SDK, Bedrock integration, Pydantic, and a static dashboard. The new workflow currently requires a single host with a persistent database file. Shared cloud storage, real email integration, authenticated operators, and production notifications remain future work. AgentCore and EventBridge are not deployed components of this revision.

## Submission assets to finish

- Verify live Bedrock tools in the intended AWS environment.
- Deploy this revision with appropriate persistent storage; the old Lambda URL is not evidence that this upgrade is deployed.
- Record a working video, maximum five minutes, using docs/DEMO_SCRIPT.md.
- Confirm https://github.com/mofeed28/stateguard is public and MIT licensing is visible.
- Supply the verified demo URL, AWS Builder ID, and current architecture diagram.
- Publish qualifying AWS Builder posts only after checking their claims against actual results.

This packet is a factual draft, not a submitted Devpost entry.
