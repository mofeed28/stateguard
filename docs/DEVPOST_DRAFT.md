# StateGuard

## One-Line Pitch

StateGuard is a reality-check layer for autonomous agents: it catches the gap between what an agent believes happened and what actually happened before the next risky action runs.

## Problem

Background agents are starting to send messages, schedule work, place orders, update records, and operate systems while humans are away. The dangerous failures are not always bad prompts or bad tools. They happen when the agent's internal state becomes false: a provider times out, a fill arrives late, a calendar invite is not accepted, or a payment does not settle.

The agent may confidently continue from an outdated belief while the real world has already moved. Those reconciliation checks are repetitive and easy to miss, but the consequences can be expensive.

## Solution

StateGuard runs in the background as a Strands-based safety agent. It ingests planned actions, local belief snapshots, external observations, and provider responses. Then it reconstructs the timeline, detects belief-vs-reality mismatches, classifies risk, and only asks the human for approval when action is actually needed.

The demo makes the agent workflow visible instead of hiding it behind a single answer: Supervisor routes the incident, Timeline Investigator reconstructs causality, Reality Reconciler checks outside-world truth, Risk Sentinel scores blast radius, Human Approval Agent blocks unsafe autonomy, and Handoff Writer prepares a sanitized report.

The product is intentionally not a generic log viewer. It is focused on one failure mode every serious agent platform will need to handle: autonomous systems acting from stale state.

## Demo Scenario

The main demo replays a high-risk automation incident:

1. An execution agent believes the position is zero.
2. A cancel response for a prior order is ambiguous.
3. The prior order fills after the timeout.
4. A second entry order is already live.
5. StateGuard detects duplicate-entry risk and blocks further autonomous action behind a human approval card.

The demo also includes client-communications and operations-scheduling replays. A follow-up agent moves on after marking an email as sent, while provider state shows the email was rejected. A scheduling agent cancels backup outreach because it believes three volunteers are confirmed, while calendar reality shows one accepted invite and two pending invites. These show the same belief-vs-reality reconciliation pattern outside finance.

## How It Uses Strands Agents

- Supervisor Agent routes the incident.
- Timeline Investigator reconstructs causality.
- Reality Reconciler compares expected and observed state.
- Risk Sentinel classifies severity.
- Human Approval Agent prepares the approval card.
- Handoff Writer generates a sanitized report.
- Custom `@tool` functions expose incident loading, mismatch detection, risk classification, and handoff generation.
- Pydantic models provide structured, validated output for the web dashboard and approval flow.
- The dashboard exposes a step-by-step workflow trace, structured decision output, and observability events so judges can see the Strands/AWS production story directly.

## Target Users

Small teams and professionals who rely on autonomous agents or bots but do not have a full operations team watching every background action.

## AWS Architecture

StateGuard can run on Amazon Bedrock/AgentCore with EventBridge for event ingestion, SQS for investigation jobs, DynamoDB for incident state, ECS/Lambda for the API and workers, and CloudWatch/OpenTelemetry-style events for production operations.

Architecture diagram: `docs/architecture-diagram.html`

## Why It Can Win

Most agent safety demos focus on prompt guardrails. StateGuard focuses on operational truth: whether the agent's memory of the world still matches the world before it acts again. That makes the demo concrete, extensible across domains, and directly useful for people running real background agents.

The project ships with a working AWS-hosted demo, deterministic replays across three domains, a custom mismatch simulator, visible Strands-style agent orchestration, structured output, approval gating, and production-shaped observability events.
