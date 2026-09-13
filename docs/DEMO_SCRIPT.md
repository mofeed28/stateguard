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
