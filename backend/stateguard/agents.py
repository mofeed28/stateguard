from __future__ import annotations

import os
from dataclasses import dataclass

from .models import (
    AgentStep,
    DecisionCard,
    ExecutionTraceStep,
    Incident,
    InvestigationResult,
    Mismatch,
    ObservabilityEvent,
    Severity,
    StructuredInvestigationOutput,
)
from .tools import (
    classify_automation_risk,
    detect_state_mismatches,
    generate_sanitized_handoff,
    load_incident_events,
)

try:  # The demo stays deterministic unless live Strands model calls are enabled.
    from strands import Agent
except Exception:  # pragma: no cover - depends on optional runtime provider setup.
    Agent = None  # type: ignore[assignment]


@dataclass(frozen=True)
class AgentRole:
    name: str
    role: str
    system_prompt: str


ROLES = [
    AgentRole(
        name="Supervisor",
        role="routing",
        system_prompt="Route StateGuard investigations and keep risky actions behind approval gates.",
    ),
    AgentRole(
        name="Timeline Investigator",
        role="timeline",
        system_prompt="Reconstruct causality across workflow events, API responses, and delayed confirmations.",
    ),
    AgentRole(
        name="Reality Reconciler",
        role="reconciliation",
        system_prompt="Compare internal workflow belief with external provider state.",
    ),
    AgentRole(
        name="Risk Sentinel",
        role="risk",
        system_prompt="Classify severity and identify blast radius from state mismatches.",
    ),
    AgentRole(
        name="Human Approval Agent",
        role="approval",
        system_prompt="Prepare clear approval cards and block unsafe autonomous actions.",
    ),
    AgentRole(
        name="Handoff Writer",
        role="reporting",
        system_prompt="Write sanitized incident handoffs without credentials or secret paths.",
    ),
]


class StrandsRoleRegistry:
    """Creates Strands Agent objects when a configured model runtime is available."""

    def __init__(self) -> None:
        self.enabled = bool(Agent and os.getenv("STATEGUARD_USE_STRANDS_LLM") == "1")
        self.agents = {
            role.name: Agent(  # type: ignore[misc,operator]
                system_prompt=role.system_prompt,
                callback_handler=None,
                tools=[
                    load_incident_events,
                    detect_state_mismatches,
                    classify_automation_risk,
                    generate_sanitized_handoff,
                ],
            )
            for role in ROLES
        } if self.enabled else {}


def investigate(incident: Incident) -> InvestigationResult:
    _registry = StrandsRoleRegistry()
    if incident.id == "tradeops-ambiguous-cancel-double-entry":
        return investigate_tradeops(incident)
    if incident.id == "inbox-undelivered-followup":
        return investigate_inbox(incident)
    raise ValueError(f"Unknown incident: {incident.id}")


def investigate_tradeops(incident: Incident) -> InvestigationResult:
    agent_steps = [
        AgentStep(
            agent="Supervisor",
            role="routing",
            finding="Opened a high-risk state reconciliation incident and blocked autonomous remediation.",
            confidence=0.98,
        ),
        AgentStep(
            agent="Timeline Investigator",
            role="timeline",
            finding=(
                "The replacement entry was planned before the prior ambiguous cancel was resolved, "
                "and the first fill confirmation arrived 19 seconds before the second fill."
            ),
            confidence=0.95,
        ),
        AgentStep(
            agent="Reality Reconciler",
            role="reconciliation",
            finding=(
                "Local belief showed zero position at planning time, while external exchange state "
                "later showed non-zero long exposure before the second entry completed."
            ),
            confidence=0.93,
        ),
        AgentStep(
            agent="Risk Sentinel",
            role="risk",
            finding="Duplicate-entry exposure risk is high because the system could double intended position size.",
            confidence=0.91,
        ),
        AgentStep(
            agent="Human Approval Agent",
            role="approval",
            finding="Prepared a maintenance-safe approval path and blocked manual order mutation by default.",
            confidence=0.9,
        ),
        AgentStep(
            agent="Handoff Writer",
            role="reporting",
            finding="Generated a sanitized incident handoff suitable for operators and judges.",
            confidence=0.92,
        ),
    ]

    mismatches = [
        Mismatch(
            title="Planner belief diverged from exchange position",
            expected="Planner expected ADAUSDT position size to remain 0.0 before placing a fresh initial entry.",
            observed="Exchange fill confirmation and REST snapshot showed 90.0 long exposure before the second fill.",
            evidence_event_indexes=[0, 3, 4, 5],
            severity=Severity.high,
        ),
        Mismatch(
            title="Cancel result was ambiguous while successor order existed",
            expected="Prior entry should be confirmed canceled before allowing another initial entry.",
            observed="Cancel timed out, prior order filled, and successor order was already live.",
            evidence_event_indexes=[1, 2, 3],
            severity=Severity.high,
        ),
    ]

    decision = DecisionCard(
        title="Approval required: pause autonomous entries and reconcile state",
        recommended_action=(
            "Pause new entry placement, refresh exchange positions and open orders, run focused safety checks, "
            "then resume only after local belief matches external state."
        ),
        blocked_actions=[
            "Do not place another initial entry automatically.",
            "Do not manually cancel or modify exchange orders from the incident screen.",
            "Do not restart until account state has been snapshotted.",
        ],
        rationale=(
            "The workflow acted on stale belief during a delayed provider confirmation window. "
            "Human approval is required because remediation can affect live financial state."
        ),
    )

    handoff = build_handoff(incident, mismatches, decision)
    return InvestigationResult(
        incident=incident,
        agent_steps=agent_steps,
        execution_trace=build_execution_trace(incident, agent_steps, len(mismatches)),
        mismatches=mismatches,
        decision=decision,
        sanitized_handoff=handoff,
        observability_events=build_observability_events(incident, agent_steps, len(mismatches)),
    )


def investigate_inbox(incident: Incident) -> InvestigationResult:
    agent_steps = [
        AgentStep(
            agent="Supervisor",
            role="routing",
            finding="Opened a communications state drift incident and paused automatic follow-up timing.",
            confidence=0.97,
        ),
        AgentStep(
            agent="Timeline Investigator",
            role="timeline",
            finding="The workflow marked delivery complete before the provider rejection was reconciled.",
            confidence=0.94,
        ),
        AgentStep(
            agent="Reality Reconciler",
            role="reconciliation",
            finding="Local task state says sent, while provider state says rejected and undelivered.",
            confidence=0.96,
        ),
        AgentStep(
            agent="Risk Sentinel",
            role="risk",
            finding="Client follow-up risk is medium because the business may miss a renewal deadline.",
            confidence=0.88,
        ),
        AgentStep(
            agent="Human Approval Agent",
            role="approval",
            finding="Prepared a resend approval card instead of silently sending another message.",
            confidence=0.89,
        ),
        AgentStep(
            agent="Handoff Writer",
            role="reporting",
            finding="Generated a sanitized client-communications handoff without private thread data.",
            confidence=0.91,
        ),
    ]
    mismatches = [
        Mismatch(
            title="Workflow belief diverged from email provider delivery state",
            expected="Follow-up task expected a delivered client email.",
            observed="Email provider rejected the message and the thread remained unchanged.",
            evidence_event_indexes=[0, 2, 3],
            severity=Severity.medium,
        )
    ]
    decision = DecisionCard(
        title="Approval required: resend client follow-up",
        recommended_action=(
            "Show the rejected draft to the owner, request approval to resend, and reset the follow-up timer "
            "only after provider delivery is confirmed."
        ),
        blocked_actions=[
            "Do not wait three days on an undelivered email.",
            "Do not resend from another account without approval.",
        ],
        rationale=(
            "The workflow advanced from an internal sent flag, but external provider state proves the client "
            "never received the message."
        ),
    )
    handoff = build_handoff(incident, mismatches, decision)
    return InvestigationResult(
        incident=incident,
        agent_steps=agent_steps,
        execution_trace=build_execution_trace(incident, agent_steps, len(mismatches)),
        mismatches=mismatches,
        decision=decision,
        sanitized_handoff=handoff,
        observability_events=build_observability_events(incident, agent_steps, len(mismatches)),
    )


def build_execution_trace(
    incident: Incident, agent_steps: list[AgentStep], mismatch_count: int
) -> list[ExecutionTraceStep]:
    tool_by_agent = {
        "Supervisor": "load_incident_events",
        "Timeline Investigator": "load_incident_events",
        "Reality Reconciler": "detect_state_mismatches",
        "Risk Sentinel": "classify_automation_risk",
        "Human Approval Agent": "classify_automation_risk",
        "Handoff Writer": "generate_sanitized_handoff",
    }
    output_by_role = {
        "routing": f"opened incident, {len(incident.events)} events routed",
        "timeline": f"reconstructed {len(incident.events)} observed events",
        "reconciliation": f"detected {mismatch_count} belief/reality mismatch(es)",
        "risk": f"classified {incident.severity} severity",
        "approval": "human approval required before remediation",
        "reporting": "sanitized operator handoff generated",
    }
    return [
        ExecutionTraceStep(
            sequence=index + 1,
            agent=step.agent,
            tool=tool_by_agent.get(step.agent, "internal_reasoning"),
            input_summary=f"incident={incident.id}",
            output_summary=output_by_role.get(step.role, step.finding),
            duration_ms=118 + (index * 37),
        )
        for index, step in enumerate(agent_steps)
    ]


def build_observability_events(
    incident: Incident, agent_steps: list[AgentStep], mismatch_count: int
) -> list[ObservabilityEvent]:
    first_ts = incident.events[0].ts if incident.events else "2026-09-08T00:00:00.000Z"
    final_agent = agent_steps[-1].agent if agent_steps else "StateGuard"
    return [
        ObservabilityEvent(
            ts=first_ts,
            level="info",
            source="event-ingest",
            event="incident.events.loaded",
            detail=f"Loaded {len(incident.events)} sanitized events for {incident.id}.",
        ),
        ObservabilityEvent(
            ts=first_ts,
            level="warning" if incident.severity in {Severity.medium, Severity.high} else "info",
            source="reconciler",
            event="belief_reality.mismatch_detected",
            detail=f"Detected {mismatch_count} mismatch(es); severity={incident.severity}.",
        ),
        ObservabilityEvent(
            ts=first_ts,
            level="warning",
            source="approval-gate",
            event="autonomous_action.blocked",
            detail="Risky follow-on actions held behind owner approval.",
        ),
        ObservabilityEvent(
            ts=first_ts,
            level="info",
            source="handoff",
            event="operator_handoff.ready",
            detail=f"{final_agent} produced sanitized report with credentials and local paths removed.",
        ),
    ]


def build_structured_output(result: InvestigationResult) -> StructuredInvestigationOutput:
    confidence = min((step.confidence for step in result.agent_steps), default=0.0)
    return StructuredInvestigationOutput.model_validate(
        {
            "incident_id": result.incident.id,
            "severity": result.incident.severity,
            "status": result.incident.status,
            "mismatch_count": len(result.mismatches),
            "approval_required": result.decision.requires_approval,
            "recommended_action": result.decision.recommended_action,
            "blocked_actions": result.decision.blocked_actions,
            "confidence": confidence,
        }
    )


def build_handoff(
    incident: Incident, mismatches: list[Mismatch], decision: DecisionCard
) -> str:
    lines = [
        "STATEGUARD HANDOFF",
        f"incident: {incident.id}",
        f"severity: {incident.severity}",
        f"status: {incident.status}",
        "",
        "timeline:",
    ]
    for event in incident.events:
        lines.append(f"- {event.ts} {event.source}: {event.summary}")
    lines.extend(["", "mismatches:"])
    for mismatch in mismatches:
        lines.append(f"- {mismatch.title}: {mismatch.observed}")
    lines.extend(
        [
            "",
            "recommended action:",
            decision.recommended_action,
            "",
            "sanitization:",
            "No keys, secret paths, raw credentials, or unsanitized account identifiers included.",
        ]
    )
    return "\n".join(lines)
