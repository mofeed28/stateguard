# StateGuard

StateGuard prevents an email worker from retrying against stale delivery state. It checks the provider ledger before sending, holds uncertain actions, and asks the owner only when a confirmed contradiction needs reconciliation.

## Working demo

The flagship is an **executable, stateful email-provider sandbox**. The sandbox sends no actual email. The separate Real Gmail proof below verifies an existing authorized self-email. Archived trading and scheduling examples remain clearly labeled read-only fixture replays.

1. Start the “Provider delivered, worker saw timeout” workflow.
2. Run the worker. The provider ledger remains at one delivery and the retry is blocked.
3. Optionally run **Investigate with live Strands**. The agent queries worker history and fresh provider evidence through tools, produces a structured diagnosis, and records actual tool outputs and measured durations.
4. Approve reconciliation. The worker updates its belief, verifies delivery, and completes without sending again.
5. Try healthy, pending, and unavailable-provider scenarios. Healthy work completes without approval; uncertain work waits for fresh evidence.

Approval includes an observed state version. A provider change invalidates old approval. SQLite transactions locally and DynamoDB conditional writes on AWS protect the sandbox against concurrent retries. Repeated completed operations have no additional effect.

## Run locally

```bash
python -m pip install -e ".[dev]"
python -m uvicorn stateguard.app:app --app-dir backend --host 127.0.0.1 --port 8787
```

Open http://127.0.0.1:8787. By default the SQLite sandbox database is in the system temporary directory. Set `STATEGUARD_DB_PATH` to a durable file for persistence across restarts. API and worker must use the same path.

For autonomous processing, start a second process (after installing the package):

```bash
python -m stateguard.worker --interval 5
```

The worker processes healthy work quietly and holds pending evidence without repeated events. Confirmed conflicts become approval cards. With live mode enabled, the worker also invokes Strands on new conflicts. The dashboard refreshes current workflow state every five seconds. It does not send notifications externally.

## Live Strands / Bedrock

Configure these environment variables using your normal AWS credential chain:

```text
STATEGUARD_USE_STRANDS_LLM=1
STATEGUARD_BEDROCK_MODEL_ID=amazon.nova-micro-v1:0
AWS_REGION=us-east-1
STATEGUARD_LIVE_DEMO_KEY=<your demo access key>
```

The chosen model must be available to your AWS account and execution role. The live route requires the demo key. Credentials never belong in source code or the browser. Agent turns/output are bounded, and provider request timeouts are configured. A failed live investigation returns an error; it is never displayed as successful AI analysis.

The live agent has two read-only tools: `inspect_worker_history` and `query_delivery_provider`. Both must be called for an investigation to be accepted. Analysis is advisory; the deterministic transaction gate owns authorization and sends. Evidence changes invalidate stored analysis. The SDK invocation is implemented and tested with an injected test agent; an actual Bedrock invocation still needs verification in the configured AWS environment.

## Validation

```bash
python -m pytest -q
python scripts/evaluate.py
```

See `docs/evaluation.json` for a reproducible four-scenario sandbox evaluation. It does not establish production effectiveness, customer savings, or LLM accuracy. Tests additionally exercise concurrent retries, duplicate approvals, stale approval, background processing, and redaction.

## Deployment scope

The full app runs on AWS Lambda with shared DynamoDB state, Secrets Manager credentials and an EventBridge sandbox worker. See `docs/DEPLOYMENT.md` for the URL and update procedure, and `docs/aws-live-verification.json` for evidence. Local development uses SQLite. GitHub pushes do not deploy automatically.

Read-only fixture traces, confidence values, and illustrative AWS architecture are not claims of live multi-agent operation. The old text simulator is an offline preview; identical statements produce no mismatch, and other free text requires external verification. Handoff redaction is best-effort, not a complete privacy guarantee.

## Submission

Track: Professional Agents. The concrete audience is small teams operating client-communication automations. See `docs/DEMO_SCRIPT.md`, `docs/SUBMISSION_PACKET.md`, and `docs/ARCHITECTURE.md` for current materials. MIT licensed.

### OpenAI through Strands (local demo)

Install `python -m pip install -e ".[dev]"`. Add `OPENAI_API_KEY=...` to the
root `.env` (gitignored), then run:

```powershell
./scripts/start-local.ps1 -Live -Provider openai
```

The workflow uses `gpt-5-mini` with low reasoning effort, bounded turns/output,
and no automatic retries. Reports include provider, model, usage and evidence.
Messages remain simulated. The legacy custom-text live preview remains Bedrock-only.
Use the contents of `.stateguard-live-key` in the masked local demo access field, never the OpenAI API key.
For the separate worker, also set `STATEGUARD_MODEL_PROVIDER=openai` and
`STATEGUARD_USE_STRANDS_LLM=1` in its process.

## Real Gmail proof (separate CLI)

The sandbox section uses simulated delivery. The Real Gmail proof section now
loads the authorized self-email, queries fresh Gmail metadata, runs a real Strands
investigation and reconciles local belief after approval. It has no send capability.
The separate Gmail CLI is used only to create an explicitly authorized self-test. Install `python -m pip install -e ".[gmail]"`, save a
Desktop OAuth client as `.secrets/gmail-client.json`, and run
`python scripts/connect_gmail.py`. Tokens stay in the Git-excluded `.secrets/` folder.

Only after explicitly authorizing a real self-email, run
`python scripts/gmail_delivery_demo.py --send-approved-self-test`.
This sends the fixed subject "StateGuard delivery test" and body
"Controlled StateGuard demo. No action needed." to the authenticated account itself.
An exclusive, flushed attempt record is saved before sending. Existing or damaged
records cannot authorize a second send. The demo deliberately withholds the send
acknowledgment from the worker; this is injected uncertainty, not a genuine outage.
Recheck without sending using `python scripts/gmail_delivery_demo.py --check-only`.
Never remove the attempt record to retry an uncertain send.

Gmail rewrote the client Message-ID during the verified test. The checker therefore
supports weaker correlation by exact subject, account and a narrow send window.
It requires one matching record carrying both SENT and INBOX labels for this
self-email proof. This is not a Gmail idempotency or general exactly-once guarantee.

The 2:36 video in `artifacts/demo/StateGuard-demo.mp4` documents the earlier sandbox
flow with real OpenAI analysis. It does not show the later Gmail experiment.
AWS now includes the upgraded app. Devpost submission and uploaded attachments are managed separately.

### Conduct the existing-message Gmail demo

Start `./scripts/start-local.ps1 -Live -Provider openai` after Gmail authorization.
In **Real Gmail proof**, enter the local demo access key, load the existing attempt,
check Gmail evidence, investigate with Strands, then reconcile verified receipt.
All Gmail endpoints require the local key, even when live models are disabled.
The agent receives only the saved claim facts and scoped counts/correlation notes,
not mailbox addresses or message bodies. The approval handler rechecks Gmail and
validates the local version before reconciling. Gmail checks and state updates
are not a distributed transaction. The same durable claim remains in place.

`docs/gmail-live-verification.json` records a completed real run. The new narrated
walkthrough is `artifacts/gmail-demo/StateGuard-demo.mp4`; it uses actual app
screenshots, edited for narration, and is not an uninterrupted screen recording.
The old sandbox video is retained separately. No new email was sent for this run.

## Additional submission resources

See `docs/FINAL_SUBMISSION_RUNBOOK.md` for the earlier submission checklist; its fixture-era deployment claims must be revalidated against this revision. The architecture diagram is served at `/architecture`. Bedrock can use `STATEGUARD_BEDROCK_MODEL_ID=us.amazon.nova-micro-v1:0` when cross-region inference permissions and quotas allow it.
