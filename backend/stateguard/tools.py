from __future__ import annotations

from typing import Any

try:
    from strands import tool
except Exception:  # pragma: no cover - import depends on optional runtime.
    def tool(func=None, **_kwargs):  # type: ignore[no-redef]
        if func is None:
            return lambda wrapped: wrapped
        return func

from .fixtures import get_incident, tradeops_incident


@tool
def load_incident_events(incident_id: str) -> dict[str, Any]:
    """Load sanitized workflow events for an incident.

    Args:
        incident_id: Stable incident identifier to investigate.
    """
    incident = get_incident(incident_id)
    if not incident:
        return {"status": "error", "reason": "incident_not_found"}
    return {"status": "success", "incident": incident.model_dump(mode="json")}


@tool
def detect_state_mismatches(incident_id: str) -> dict[str, Any]:
    """Detect belief-vs-reality mismatches for an autonomous workflow incident.

    Args:
        incident_id: Stable incident identifier to analyze.
    """
    incident = get_incident(incident_id)
    if not incident:
        return {"status": "error", "reason": "incident_not_found"}

    from .agents import investigate

    return {"status": "success", "mismatches": [item.model_dump(mode="json") for item in investigate(incident).mismatches]}


@tool
def classify_automation_risk(incident_id: str) -> dict[str, Any]:
    """Classify the operational risk and blocked autonomous actions.

    Args:
        incident_id: Stable incident identifier to classify.
    """
    incident = get_incident(incident_id)
    if not incident:
        return {"status": "error", "reason": "incident_not_found"}

    from .agents import investigate

    result = investigate(incident)

    return {
        "status": "success",
        "severity": result.incident.severity,
        "risk": result.decision.title,
        "blocked_actions": result.decision.blocked_actions,
    }


@tool
def generate_sanitized_handoff(incident_id: str) -> dict[str, str]:
    """Generate a sanitized operator handoff for an incident.

    Args:
        incident_id: Stable incident identifier to summarize.
    """
    from .agents import investigate

    incident = get_incident(incident_id)
    if not incident:
        return {"status": "error", "handoff": "incident_not_found"}
    return {"status": "success", "handoff": investigate(incident).sanitized_handoff}
