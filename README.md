# StateGuard

StateGuard is an AI operations safety agent for autonomous workflows. It compares what a background agent believes happened with what the outside world says happened, reconstructs the timeline, classifies risk, and asks for human approval only when action is needed.

The hackathon demo uses a trading automation incident because the failure mode is concrete: an automated system believes a cancel/fill sequence is safe, while external state shows a duplicate-entry risk.

## Why It Matters

Autonomous agents increasingly send emails, schedule people, place orders, update systems, and run background operations. Failures often happen in the gap between internal belief and real-world state:

- An order cancellation times out, but the order still exists.
- A fill is delayed, so the planner thinks position size is zero.
- A message agent thinks an email was sent, but the provider rejected it.
- A scheduler believes a volunteer accepted, but no calendar slot was confirmed.

StateGuard is the safety layer for that gap.

## Demo

Live AWS demo:

```text
https://gzmrlkrayb3oz3qe22g2v5tv7e0qoqfa.lambda-url.us-east-1.on.aws/
```

Run locally:

```bash
cd stateguard
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
uvicorn stateguard.app:app --app-dir backend --reload --port 8787
```

Open `http://127.0.0.1:8787`.

Run smoke checks against a live local or hosted app:

```bash
STATEGUARD_BASE_URL=http://127.0.0.1:8787 scripts/smoke.sh
```

The flagship demo incident replays a high-risk automation mismatch:

1. Bot plans an entry while its local position belief is zero.
2. Exchange fill recognition is delayed.
3. A prior order may still exist after an ambiguous cancel response.
4. StateGuard reconstructs the timeline, spots belief-vs-reality drift, and asks for approval before a safe maintenance action.

The dashboard also includes client-communications and operations-scheduling incidents. One follow-up agent believes an email was sent, but the provider rejected delivery. Another scheduling agent believes a clinic shift is fully staffed, but the calendar still has two pending volunteers. These prove the core product is not finance-only: it is a generic reconciliation layer with a specific, high-stakes flagship demo.

The app now shows the full investigation run:

- Incident timeline
- Agent role findings
- Strands workflow trace
- Validated structured output
- State mismatches
- Human approval card
- Observability event stream
- Sanitized handoff report
- Custom mismatch simulator with before/after outcome
- Optional live Strands analysis endpoint with deterministic fallback

The 90-second video outline lives in `docs/DEMO_SCRIPT.md`, the paste-ready Devpost packet lives in `docs/SUBMISSION_PACKET.md`, and the final submission runbook lives in `docs/FINAL_SUBMISSION_RUNBOOK.md`.

## Architecture

Open the standalone architecture diagram at [`docs/architecture-diagram.html`](docs/architecture-diagram.html).

StateGuard is built around Strands-style agent roles:

- **Supervisor Agent** routes the investigation.
- **Timeline Investigator** reconstructs causality from logs/events.
- **Reality Reconciler** compares internal belief with observed external state.
- **Risk Sentinel** classifies severity and blast radius.
- **Human Approval Agent** prepares decision cards instead of taking risky action directly.
- **Handoff Writer** generates a sanitized incident report.

The implementation also exposes Strands custom function tools:

- `load_incident_events`
- `detect_state_mismatches`
- `classify_automation_risk`
- `generate_sanitized_handoff`

These are defined with the Strands `@tool` decorator and can be passed directly to `Agent(tools=[...])`. The default local demo uses deterministic tool outputs so the project runs without credentials, while `STATEGUARD_USE_STRANDS_LLM=1` enables live Strands agent construction when a model provider is configured.

Demo API surfaces:

- `/api/incidents/{incident_id}/replay` returns the full investigation result.
- `/api/incidents/{incident_id}/structured-output` returns a Pydantic-validated decision object suitable for Strands structured output.
- `/api/incidents/{incident_id}/observability` returns production-style events for CloudWatch/OpenTelemetry mapping.
- `/api/simulate-mismatch` accepts custom belief/reality/action text and returns a structured approval decision.
- `/api/simulate-mismatch/live` runs the same request through optional live Strands/Bedrock analysis when enabled. Paid live calls are protected by a demo key, and the endpoint falls back safely when live mode is disabled or unavailable.

The current demo is deterministic and fixture-backed so judges can run it without exchange keys or private credentials. Live adapters can be added for trading platforms, email providers, calendars, payment systems, and volunteer scheduling tools.

Optional live LLM mode is deliberately disabled by default. To enable it, configure Bedrock model access and set:

```bash
STATEGUARD_USE_STRANDS_LLM=1
STATEGUARD_BEDROCK_MODEL_ID=amazon.nova-micro-v1:0
STATEGUARD_LIVE_DEMO_KEY=replace-with-a-random-demo-key
STATEGUARD_LIVE_TIMEOUT_SECONDS=18
AWS_REGION=us-east-1
```

## Hackathon Fit

Track: Professional Agents

Theme fit: StateGuard handles repetitive background operational checks and only surfaces when human judgment is needed.

AWS fit: The production architecture maps cleanly to Amazon Bedrock/AgentCore for agents, EventBridge/SQS for event ingestion, DynamoDB for incident state, and ECS/Lambda for workers.

Official resources used for alignment:

- Strands quickstart: custom agents run in-process and can be embedded in FastAPI.
- Strands custom tools: Python `@tool` functions expose typed, documented capabilities to agents.
- Strands structured output: Pydantic models provide validated agent results.
- AgentCore Runtime: deployment target for containerized or direct-code agent runtimes.

## Deployment

The live hackathon demo is deployed on AWS Lambda Function URL. The repo also includes a production Dockerfile and App Runner notes in `docs/DEPLOYMENT.md`, but App Runner returned an AWS-side internal system error during provisioning on this account. AgentCore/Bedrock/EventBridge/DynamoDB remain the production architecture path.

## License

MIT
