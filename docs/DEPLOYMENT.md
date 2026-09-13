# Deployment

## Current working-tree upgrade

The stateful email workflow has not yet been deployed. Run FastAPI and the optional background worker on one host with the same persistent STATEGUARD_DB_PATH. SQLite is appropriate for this single-host sandbox; it is not shared storage across Lambda instances.

```bash
python -m pip install -e ".[dev]"
python -m uvicorn stateguard.app:app --app-dir backend --host 127.0.0.1 --port 8787
python -m stateguard.worker --interval 5
```

The worker command runs in a separate terminal. For local-only access, keep the API bound to 127.0.0.1. For a hosted container, configure the binding and persistent volume appropriately.

## Live model setup

Use an AWS profile or workload role through the normal credential chain; never commit credentials. Set AWS_REGION, STATEGUARD_USE_STRANDS_LLM=1, STATEGUARD_BEDROCK_MODEL_ID, and STATEGUARD_LIVE_DEMO_KEY. The execution identity needs Bedrock model invocation permissions and access to the selected model. User-triggered live investigation requires the demo key. The background worker uses its own configured AWS credentials and does not expose an HTTP model endpoint.

Verify actual tool calls through POST /api/workflows/{id}/investigate before recording. A 503 indicates live analysis was unavailable; there is no substituted model result. Inspect server configuration without sharing credential values.

## Historical deployment

The earlier fixture demo used Lambda function stateguard, handler stateguard.app.handler, Python 3.11, and Mangum:

https://gzmrlkrayb3oz3qe22g2v5tv7e0qoqfa.lambda-url.us-east-1.on.aws/

That URL has not been verified against this revision. Do not deploy the new stateful workflow with /tmp persistence and claim durable cross-instance operation. Replace SQLite with a shared transactional store for a scaled Lambda deployment. The supplied Dockerfile can serve as a single-host starting point; configure persistence separately.

## Production requirements

A real delivery provider adapter must provide stable message identifiers, fresh status, and idempotent sends. Add authenticated operator identity, durable audit retention, resource limits, and shared persistence before connecting real accounts. This public sandbox contains constructed examples only. No external messages or notifications are sent.
