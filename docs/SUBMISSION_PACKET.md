# StateGuard Submission Packet

## Project Title

StateGuard

## Tagline

A reality-check layer for autonomous agents before they take the next risky action.

## Short Description

StateGuard catches the gap between what an autonomous agent believes happened and what actually happened in the outside world. It reconstructs the timeline, detects state mismatches, classifies risk, and asks for human approval only when intervention is needed.

## Live Demo

https://gzmrlkrayb3oz3qe22g2v5tv7e0qoqfa.lambda-url.us-east-1.on.aws/

## Source Repository

https://github.com/mofeed28/stateguard

Final submission note: Devpost requires this repository URL to be public. The repo can remain private during prep, then be flipped public before submitting.

Architecture diagram: `docs/architecture-diagram.html`

## What It Does

StateGuard monitors autonomous workflows for belief-vs-reality drift. The demo shows an execution agent that believes a trading position is zero and plans a fresh entry. External exchange events tell a different story: an earlier cancel was ambiguous, the prior order filled, and the workflow is now at risk of doubling exposure.

StateGuard catches that mismatch before the next autonomous action. It shows the investigation timeline, agent findings, structured output, risk classification, approval gate, observability events, and a sanitized operator handoff.

The project also includes client-communications and operations-scheduling incidents. One agent believes an email was sent, but the provider rejected delivery. Another believes a clinic shift is fully staffed, but calendar reality shows only one accepted volunteer and two pending invites. That shows the same safety pattern works beyond finance.

Judges can also use the custom mismatch simulator to enter their own domain, agent belief, external reality, and risky next action. StateGuard returns a structured approval decision and a before/after comparison showing what happens without the safety layer versus with it.

## Why It Matters

Most agent safety work focuses on prompts, content filters, and tool permissions. Those are important, but real operations fail in another way: the agent's internal state becomes false. A provider times out, an external system changes, an event arrives late, and the agent confidently continues from a stale belief.

StateGuard focuses on operational truth. Before an agent continues, it checks whether the agent's memory of the world still matches the world.

## How We Built It

StateGuard is a FastAPI application with a static dashboard and deterministic incident fixtures for judge-friendly replay. The backend models incidents, workflow events, mismatches, agent steps, execution traces, decision cards, structured outputs, and observability events with Pydantic.

The agent workflow is organized as Strands-style roles:

- Supervisor Agent routes the incident.
- Timeline Investigator reconstructs causality.
- Reality Reconciler compares internal belief with external state.
- Risk Sentinel classifies severity and blast radius.
- Human Approval Agent blocks unsafe follow-up actions behind approval.
- Handoff Writer produces a sanitized report.

Custom Strands `@tool` functions expose incident loading, mismatch detection, risk classification, and handoff generation. The live demo uses deterministic tool outputs so it can run without exchange keys, email credentials, or private data.

## AWS Usage

The live demo is hosted on AWS using Lambda with a public Function URL. The app uses Mangum to run FastAPI on Lambda.

The production architecture maps to:

- Amazon Bedrock or AgentCore for agent runtime
- EventBridge for event ingestion
- SQS for investigation jobs
- DynamoDB for incident state
- Lambda or ECS for API and workers
- CloudWatch/OpenTelemetry-style events for observability

App Runner and Docker deployment files are included in the repository. App Runner was the original target, but provisioning hit an AWS-side internal error on this account, so Lambda Function URL became the reliable live demo path.

## Challenges

The main challenge was making an agent-safety idea concrete enough to judge quickly. Generic monitoring is too broad, so we narrowed the project to one failure mode: autonomous systems acting from stale state.

Deployment also required a pivot. App Runner connected to GitHub and built the service, but AWS returned an internal provisioning error. We switched to Lambda Function URL to keep the demo AWS-hosted and reliable.

## What Is Next

Next steps are live adapters for real workflow systems: trading platforms, inbox providers, calendars, payment processors, and project-management tools. StateGuard can then ingest actual provider events, compare them with agent belief snapshots, and block unsafe continuation until the mismatch is resolved.

## Recording Checklist

1. Open the live URL.
2. Start on the top cards: Agent believed, Reality showed, StateGuard blocked.
3. Click Replay Incident.
4. Scroll through timeline and agent findings.
5. Show State Mismatches.
6. Show Decision Card and approval gate.
7. Show Strands Workflow Trace.
8. Show Structured Output.
9. Show Observability Events.
10. Close on the line: StateGuard checks whether the agent's memory of the world still matches the world before it acts again.
