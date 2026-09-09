from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Severity(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class EventKind(StrEnum):
    planned_action = "planned_action"
    local_belief = "local_belief"
    external_observation = "external_observation"
    provider_response = "provider_response"
    fill_confirmation = "fill_confirmation"
    agent_note = "agent_note"


class WorkflowEvent(BaseModel):
    ts: str
    kind: EventKind
    source: str
    summary: str
    data: dict[str, Any] = Field(default_factory=dict)


class Mismatch(BaseModel):
    title: str
    expected: str
    observed: str
    evidence_event_indexes: list[int]
    severity: Severity


class AgentStep(BaseModel):
    agent: str
    role: str
    finding: str
    confidence: float = Field(ge=0, le=1)


class ExecutionTraceStep(BaseModel):
    sequence: int
    agent: str
    tool: str
    input_summary: str
    output_summary: str
    duration_ms: int


class ObservabilityEvent(BaseModel):
    ts: str
    level: str
    source: str
    event: str
    detail: str


class DecisionCard(BaseModel):
    title: str
    recommended_action: str
    requires_approval: bool = True
    blocked_actions: list[str] = Field(default_factory=list)
    rationale: str


class Incident(BaseModel):
    id: str
    title: str
    domain: str
    status: str
    severity: Severity
    user: str
    summary: str
    events: list[WorkflowEvent]


class InvestigationResult(BaseModel):
    incident: Incident
    agent_steps: list[AgentStep]
    execution_trace: list[ExecutionTraceStep]
    mismatches: list[Mismatch]
    decision: DecisionCard
    sanitized_handoff: str
    observability_events: list[ObservabilityEvent]


class StructuredInvestigationOutput(BaseModel):
    incident_id: str
    severity: Severity
    status: str
    mismatch_count: int
    approval_required: bool
    recommended_action: str
    blocked_actions: list[str]
    confidence: float = Field(ge=0, le=1)


class CustomMismatchRequest(BaseModel):
    domain: str = Field(min_length=2, max_length=80)
    agent_belief: str = Field(min_length=8, max_length=500)
    external_reality: str = Field(min_length=8, max_length=500)
    risky_action: str = Field(min_length=8, max_length=300)


class CustomMismatchResponse(BaseModel):
    result: InvestigationResult
    structured_output: StructuredInvestigationOutput
    without_stateguard: str
    with_stateguard: str
    live_mode: bool = False
    live_model: str | None = None
    live_error: str | None = None
