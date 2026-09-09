# Demo Script

Target length: 90 seconds.

## Opening

StateGuard is a reality-check layer for autonomous agents. It catches the gap between what an agent believes happened and what actually happened before the next risky action runs.

## Problem

Background agents do useful work while humans are away: they send messages, schedule work, place orders, and update systems. But the dangerous failures happen when the agent's internal state becomes stale. A provider times out, a fill arrives late, or an external system rejects a request, and the agent keeps moving as if its belief is still true.

## Demo

In this replay, an execution agent believes the position is zero, so it plans a fresh entry. But the exchange tells a different story: an earlier cancel response was ambiguous, and the prior order fills anyway. StateGuard reconstructs the timeline, compares belief against external reality, and detects duplicate-entry risk before the workflow can continue.

The dashboard shows the investigation path: Supervisor, Timeline Investigator, Reality Reconciler, Risk Sentinel, Human Approval Agent, and Handoff Writer. The result is not just an alert. StateGuard produces structured output, blocks unsafe autonomous actions, and creates a sanitized handoff for the operator.

The same pattern also appears in communications and scheduling: an email marked sent even though the provider rejected it, and a clinic shift marked covered even though calendar confirmations are still pending. The point is broader than trading. StateGuard is for any autonomous workflow where stale state can trigger bad real-world action.

Now switch to the custom simulator. Enter a simple invoice mismatch: the agent believes invoice #104 is paid, but the bank API says it is unpaid. StateGuard creates the same approval-gated decision path from fresh input, which shows the product is not only a set of pre-cooked replays.

Mention that the Live Strands Analysis button is optional. The core demo remains deterministic for reliability, while the live path can call a Strands Agent with Bedrock when model access is enabled. Paid live calls are protected by a demo key so the public URL cannot drain credits.

## AWS And Strands

The demo is running on AWS with a public Lambda Function URL. The production shape maps to Strands agents with custom tools, EventBridge or SQS for event ingestion, DynamoDB for incident state, and CloudWatch-style observability.

## Close

Most agent safety tools focus on prompts. StateGuard focuses on operational truth: whether the agent's memory of the world still matches the world before it acts again.
