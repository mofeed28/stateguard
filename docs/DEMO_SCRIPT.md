# StateGuard narrated demo

Duration: 2 minutes 36 seconds. Edited walkthrough using actual app screenshots and synthesized Windows narration. Email delivery is simulated. Live model: OpenAI gpt-5-mini through Strands.

StateGuard

A timeout does not mean an email failed. An autonomous worker can retry after the provider already delivered, sending your client the same message twice. StateGuard checks the evidence before the next action.

01 / Detect the mismatch

Here is the working application. This is an isolated, stateful email sandbox: no real email is sent. The worker believes the message was not sent, but the provider ledger already records one delivery. This disagreement is the problem we need to resolve.

02 / Stop the duplicate

We run the worker. StateGuard checks the provider and blocks the retry before another delivery occurs. The workflow now needs approval, and the delivery count stays at one. The action gate runs in a SQLite transaction, so repeated worker calls cannot create another sandbox delivery.

03 / Investigate with Strands

Now a real Strands agent investigates using OpenAI. It calls the worker history tool and the delivery provider tool to collect fresh evidence. Its structured report explains the disagreement and recommends reconciliation. The agent can advise, but it cannot send a message or approve its own recommendation.

04 / Approve and verify

We approve reconciliation through the application. This updates the worker's belief to match confirmed delivery. The workflow completes with exactly one delivery. The audit trail records the approval and verification. Approval is tied to the state version, so changed evidence cannot be overwritten by a stale decision.

05 / Avoid needless interruptions

Safety should not require a human for every action. In the healthy scenario, both sources agree the message has not been sent. The worker sends once in the sandbox and completes without human approval. When provider evidence is pending or unavailable, the worker instead holds the retry until the evidence changes.

Built and verified

The current implementation combines Strands tool use, structured analysis, a transactional action gate, versioned approvals, and persisted audit events. Twenty eight regression tests pass, including concurrent worker calls and stale approvals. These are controlled sandbox results, not a claim of production reliability.

Check reality. Verify recovery.

A real email provider adapter and shared cloud persistence are the next steps. Bedrock remains supported, while this recorded investigation uses OpenAI through Strands. StateGuard demonstrates one concrete outcome: identify the mismatch, prevent the duplicate, and verify recovery before the workflow moves on.

Video: artifacts/demo/StateGuard-demo.mp4
Captions: artifacts/demo/StateGuard-demo.srt
Not uploaded or submitted.


# Real Gmail recovery demo (new)

Duration: 2:24. Actual dashboard captures with edited narration and captions. Reuses the existing real self-email; no new mail sent.

StateGuard / Gmail

This is StateGuard with a real Gmail connection. One approved test email has already been sent to the same account. We deliberately withheld its acknowledgment from the worker. This demonstration reuses that message. It does not send another email, and it does not pretend that the injected failure was a real Gmail outage.

01 / Recover the attempt

We load the send attempt that was saved before the request. The worker belief is unknown, and retry is disabled. The durable claim prevents this demo from authorizing a second send, even after a restart. This is a conservative application safeguard, not a claim that Gmail itself offers exactly once delivery.

02 / Check real evidence

The dashboard now queries Gmail. It finds one matching message with both Sent and Inbox labels. The result includes the time of the fresh check. Gmail rewrote our original Message ID, so the interface openly shows the fallback: the exact subject, sending account, and a narrow send window. That correlation is weaker and must be reviewed.

03 / Investigate with Strands

Next, a real Strands agent investigates using OpenAI. One tool reads the saved send attempt and the injected acknowledgment loss. The other queries Gmail again. Only evidence for the approved test is returned, with mailbox addresses and message bodies excluded. The agent explains the evidence and recommends reconciliation. It has no send tool and no approval tool.

04 / Inspect the tool trace

The trace shows the actual tools called, their measured duration, and their returned evidence. The interface also reports model usage. This is the agent investigating the real Gmail test, not an archived replay. The deterministic recovery gate remains responsible for deciding whether the evidence is sufficient for approval.

05 / Reconcile, without resending

We approve reconciliation in the dashboard. The server rechecks Gmail and validates the decision version before updating local state. The worker now records delivered, recovery is complete, and retry remains disabled. The audit records the approval. Thirty five regression tests pass, including stale approvals and missing Inbox evidence. This proves one controlled self email recovery. Shared cloud storage and production reliability remain future work.
