# Final Submission Runbook

Use this as the final Devpost and demo-video checklist.

## Submit These Links

Live demo:

```text
https://gzmrlkrayb3oz3qe22g2v5tv7e0qoqfa.lambda-url.us-east-1.on.aws/
```

Source repo:

```text
https://github.com/mofeed28/stateguard
```

Important: Devpost asks for a public source repo. Keep the repo private during prep, then make it public right before final submission.

Architecture diagram:

```text
https://gzmrlkrayb3oz3qe22g2v5tv7e0qoqfa.lambda-url.us-east-1.on.aws/architecture
```

## Devpost Fields

Project title:

```text
StateGuard
```

Tagline:

```text
A reality-check layer for autonomous agents before they take the next risky action.
```

Short description:

```text
StateGuard catches the gap between what an autonomous agent believes happened and what actually happened in the outside world. It reconstructs the timeline, detects state mismatches, classifies risk, and asks for human approval only when intervention is needed.
```

What it does:

```text
StateGuard monitors autonomous workflows for belief-vs-reality drift. In the flagship demo, a trading agent believes a position is zero and plans a fresh entry, but exchange events show an ambiguous cancel and a late fill that create duplicate-entry risk. StateGuard reconstructs the timeline, compares the agent's belief with external reality, blocks unsafe continuation, and produces a human approval card with a sanitized handoff.

The same pattern appears in client communications and volunteer scheduling: an email marked sent even though the provider rejected it, and a clinic shift marked covered even though calendar confirmations are still pending. Judges can also enter their own belief/reality/action mismatch in the custom simulator and see StateGuard produce a structured decision.
```

Who it is for:

```text
StateGuard is for teams using autonomous agents in operations: trading systems, inbox agents, schedulers, payment workflows, support queues, and other background automations where stale state can trigger real-world damage.
```

Why it matters:

```text
Most agent safety tools focus on prompts, content filters, and tool permissions. Those matter, but real operational failures also happen when an agent's internal state becomes false. A provider times out, an event arrives late, an external system rejects a request, and the agent keeps moving as if its belief is still true. StateGuard checks operational truth before the next risky action.
```

How we built it:

```text
StateGuard is a FastAPI app deployed on AWS Lambda Function URL with a static dashboard and Pydantic-validated API models. The workflow is organized around Strands-style agent roles: Supervisor, Timeline Investigator, Reality Reconciler, Risk Sentinel, Human Approval Agent, and Handoff Writer.

The backend exposes custom Strands @tool functions for incident loading, mismatch detection, risk classification, and sanitized handoff generation. The stable demo uses deterministic fixtures so judges can run it without private credentials, while the optional Live Strands Analysis path can call Bedrock through Strands when model access is available. Paid live calls are protected by a demo key and fall back safely.
```

AWS usage:

```text
The live demo runs on AWS Lambda with a public Function URL and Mangum for FastAPI. The production architecture maps to Amazon Bedrock or AgentCore for the agent runtime, EventBridge for event ingestion, SQS for investigation jobs, DynamoDB for incident state, and CloudWatch/OpenTelemetry-style observability events. The repo also includes Docker/App Runner deployment files.
```

Challenges:

```text
The main challenge was making agent safety concrete enough to judge quickly. We narrowed the idea to a specific failure mode: autonomous systems acting from stale state. Deployment also required a pivot when App Runner hit an AWS-side provisioning error, so we switched to Lambda Function URL to keep the demo reliable and AWS-hosted.
```

What is next:

```text
Next steps are live adapters for real workflow systems: trading platforms, inbox providers, calendars, payment processors, and project-management tools. StateGuard can then ingest actual provider events, compare them with agent belief snapshots, and block unsafe continuation until the mismatch is resolved.
```

## Demo Video Shot List

Target length: 2 to 3 minutes. Maximum allowed: 5 minutes.

1. Open with the live URL on the top cards.
   Say: "Agents can be wrong about the state of the world. StateGuard checks reality before they act again."

2. Show the flagship trading incident.
   Click `Replay Incident`. Point to Agent believed, Reality showed, and StateGuard blocked.

3. Scroll to the timeline and findings.
   Say that StateGuard reconstructs what happened instead of trusting the agent's memory.

4. Show state mismatches and the decision card.
   Say that unsafe autonomous continuation is blocked behind human approval.

5. Show the Strands workflow trace and structured output.
   Mention Supervisor, Timeline Investigator, Reality Reconciler, Risk Sentinel, Human Approval Agent, and Handoff Writer.

6. Show observability events.
   Say this is shaped for production operations, not just a chat answer.

7. Use the sidebar to jump to Architecture.
   Click `Open diagram` and briefly show the AWS production shape.

8. Return to the app and show another incident from the dropdown.
   Use the scheduling or inbox case to prove this is multi-domain.

9. Show the custom simulator.
   Use the default invoice example and click `Simulate Mismatch`.

10. Close with the key line:
    "StateGuard is a reality-check layer for autonomous agents. It asks one question before risky automation continues: does the agent's belief still match the world?"

## Do Not Do In The Video

- Do not depend on live LLM output.
- Do not show the live demo key.
- Do not spend time explaining setup commands.
- Do not apologize for Bedrock quota. Mention optional live Strands mode only briefly.

## Final Submission Checklist

- Live demo URL works.
- Repo is public.
- MIT license visible.
- README has setup instructions.
- Architecture diagram included.
- Demo video uploaded and linked.
- AWS Builder ID added.
- Devpost text pasted from this runbook.
- Final live smoke check passes.
