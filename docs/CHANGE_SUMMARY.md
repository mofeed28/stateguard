# Executable workflow and live provider verification

Previously the main experience replayed fixture findings and displayed an approval
without enforcing a workflow transition. The new local workflow stores independent
runs in SQLite, checks provider evidence before acting, holds uncertainty, blocks
contradictions and reconciles only against a current approved version.

## Included

- Transactional sandbox gate, background worker, real audit events and dashboard controls.
- Real Strands investigations with two evidence tools, structured output, bounded
  requests, OpenAI/Bedrock selection and recorded usage. OpenAI was verified live.
- Explicit read-only fixture labeling and best-effort handoff redaction.
- Gmail OAuth setup and a separate, authorized single-self-email proof. The saved
  claim prevents automatic resend; acknowledgment loss is deliberately injected.
- Updated architecture/submission material, reproducible sandbox evaluation, and
  a narrated 1080p sandbox walkthrough with captions and original screenshot assets.

## Validation and limits

The full regression suite covers stale approvals, concurrent sandbox workers,
isolation, explicit live failures, provider configuration and durable Gmail claims.
Live OpenAI investigations called both evidence tools. One Gmail test message was
verified with SENT and INBOX labels; Gmail rewrote Message-ID, requiring the documented
subject/account/time fallback. No production effectiveness claim follows from this.

Gmail is not yet integrated into the dashboard or live agent tools. The video
predates the Gmail proof. Bedrock inference remains blocked by account quota.
Cloud deployment, shared persistence, production authentication and provider-level
idempotency remain unfinished. Secrets, mailbox evidence and local databases are
excluded from Git. The current change is a local commit, not a deployment.
