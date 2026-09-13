# StateGuard architecture

## Implemented now

```mermaid
flowchart LR
  W[Background email worker] --> G[Transactional action gate]
  P[Stateful sandbox provider ledger] --> G
  G -->|healthy| D[One sandbox delivery]
  G -->|uncertain| Q[Wait for new evidence]
  G -->|contradiction| H[Versioned approval card]
  H --> R[Revalidate and reconcile]
  R --> V[Verify delivery and complete]
  S[Strands agent on OpenAI or Bedrock] --> T[Read worker history tool]
  S --> E[Query provider evidence tool]
  T --> DB[(SQLite run state and audit log)]
  E --> DB
  S --> A[Structured diagnosis and measured tool trace]
  G --> DB
  R --> DB
```

`workflow.py` implements the sandbox state machine, provider ledger, atomic guard, approval checks, and live investigation. `worker.py` runs an independent background polling process. FastAPI exposes controls; the dashboard presents current state, real audit events, and optional model output.

Each run has a random identifier and independent state. These identifiers are demo capabilities, not a production authentication system. Approval records the expected version and permits reconciliation only; it never authorizes a resend. A provider change invalidates prior analysis and approval. The local SQLite transaction covers the sandbox evidence check and send; this atomicity does not automatically extend to an external API.

Live investigation uses a single Strands agent with two read-only evidence tools. It is not a six-agent system. The archived examples are deterministic illustrations. Pydantic validates actual live structured output. Tool output and elapsed time are recorded from execution, not synthesized.

## Required before production

Implement a real provider adapter with stable message IDs/idempotency, authenticated operator access, bounded retention, and shared durable storage. For AWS scaling, replace SQLite with conditional DynamoDB operations or another shared transactional store and enqueue worker jobs. AgentCore, EventBridge, SQS, and CloudWatch integrations remain future work. Lambda /tmp is unsuitable for shared durable state.

## Separate real-email experiment

The Gmail CLI persists a single send claim, sends one explicitly authorized self-email, injects acknowledgment loss, and checks Sent/Inbox evidence. The send operation stays in the CLI; the dashboard and agent tools now read its existing claim and verify receipt. See the README for correlation limitations and safe rechecking.

## Real Gmail dashboard recovery

`gmail_recovery.py` exposes read-only Gmail checks and a local reconciliation state
machine in its own SQLite table. The dashboard loads the existing durable claim,
checks receipt metadata, invokes two Strands tools (`inspect_send_attempt` and
`query_gmail_receipt`), and approves only after revalidation and a version check.
The Gmail dashboard and agent cannot send messages. It uses the existing self-test
from the separate CLI. Subject/account/time correlation is weaker than an immutable
provider identifier; the displayed proof is restricted to this controlled test.

## Diagram files

- `architecture-diagram.png`: selected diagram for Devpost upload.
- `architecture-diagram.svg`: editable vector version.
- `architecture-diagram.html`: browser version served at `/architecture`.

The dashed sandbox connector represents the separate test investigation path; the sandbox uses its own tools rather than the Gmail-specific tools named in the diagram.

Regenerate these files with `python scripts/render_architecture.py` (Pillow and Windows Segoe UI fonts required).
