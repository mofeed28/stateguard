# StateGuard

## One-Line Pitch

StateGuard keeps autonomous workflows honest by comparing what agents believe happened with what actually happened in the outside world.

## Problem

Background agents are starting to send messages, schedule work, place orders, update records, and operate systems while humans are away. The dangerous failures happen when an agent's internal belief diverges from external reality: a provider times out, a fill arrives late, a calendar invite is not accepted, or a payment does not settle.

Those checks are repetitive and easy to miss, but the consequences can be expensive.

## Solution

StateGuard runs in the background as a Strands-based safety agent. It ingests planned actions, local belief snapshots, external observations, and provider responses. Then it reconstructs the timeline, detects belief-vs-reality mismatches, classifies risk, and only asks the human for approval when action is needed.

The demo makes the agent workflow visible instead of hiding it behind a single answer: Supervisor routes the incident, Timeline Investigator reconstructs causality, Reality Reconciler checks outside-world truth, Risk Sentinel scores blast radius, Human Approval Agent blocks unsafe autonomy, and Handoff Writer prepares a sanitized report.

## Demo Scenario

The main demo replays a high-risk automation incident:

1. An execution agent believes the position is zero.
2. A cancel response for a prior order is ambiguous.
3. The prior order fills after the timeout.
4. A second entry order is already live.
5. StateGuard detects duplicate-entry risk and blocks further autonomous action behind a human approval card.

The demo also includes a smaller client-communications replay: a follow-up agent moves on after marking an email as sent, while provider state shows the email was rejected. This shows the same belief-vs-reality reconciliation pattern outside finance.

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
