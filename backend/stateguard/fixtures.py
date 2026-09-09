from __future__ import annotations

from .models import EventKind, Incident, Severity, WorkflowEvent


def tradeops_incident() -> Incident:
    events = [
        WorkflowEvent(
            ts="2026-08-24T17:15:58.112Z",
            kind=EventKind.local_belief,
            source="planner",
            summary="Planner snapshot shows ADAUSDT long position size as 0.0.",
            data={"symbol": "ADAUSDT", "planner_position": 0.0, "open_orders_seen": 1},
        ),
        WorkflowEvent(
            ts="2026-08-24T17:16:01.004Z",
            kind=EventKind.planned_action,
            source="execution-agent",
            summary="Entry order planned because local position belief is zero.",
            data={
                "symbol": "ADAUSDT",
                "client_order_id": "entry_initial_normal_long_8f61",
                "order_id": "sanitized-order-1027",
                "side": "buy",
            },
        ),
        WorkflowEvent(
            ts="2026-08-24T17:16:04.882Z",
            kind=EventKind.provider_response,
            source="exchange-api",
            summary="Cancel response for prior entry is ambiguous after API timeout.",
            data={
                "prior_client_order_id": "entry_initial_normal_long_25aa",
                "prior_order_id": "sanitized-order-1019",
                "response": "timeout",
                "latency_ms": 2901,
            },
        ),
        WorkflowEvent(
            ts="2026-08-24T17:16:05.327Z",
            kind=EventKind.fill_confirmation,
            source="exchange-ws",
            summary="Prior entry order fill arrives after cancel ambiguity.",
            data={
                "client_order_id": "entry_initial_normal_long_25aa",
                "order_id": "sanitized-order-1019",
                "fill_qty": 90.0,
                "position_after_fill": 90.0,
            },
        ),
        WorkflowEvent(
            ts="2026-08-24T17:16:11.410Z",
            kind=EventKind.external_observation,
            source="exchange-rest",
            summary="Fetched exchange position now shows non-zero ADAUSDT long exposure.",
            data={"symbol": "ADAUSDT", "exchange_position": 90.0, "open_orders": 1},
        ),
        WorkflowEvent(
            ts="2026-08-24T17:16:24.189Z",
            kind=EventKind.fill_confirmation,
            source="exchange-ws",
            summary="Second entry order fills while prior fill was already real externally.",
            data={
                "client_order_id": "entry_initial_normal_long_8f61",
                "order_id": "sanitized-order-1027",
                "fill_qty": 90.0,
                "position_after_fill": 180.0,
            },
        ),
    ]
    return Incident(
        id="tradeops-ambiguous-cancel-double-entry",
        title="Ambiguous cancel caused duplicate-entry risk",
        domain="High-risk automation",
        status="needs_approval",
        severity=Severity.high,
        user="Algo operator",
        summary=(
            "An execution agent acted on stale local position belief while exchange state "
            "showed a prior order could still fill."
        ),
        events=events,
    )


def inbox_incident() -> Incident:
    events = [
        WorkflowEvent(
            ts="2026-09-08T08:59:12.000Z",
            kind=EventKind.local_belief,
            source="follow-up-agent",
            summary="Agent marks client renewal follow-up as sent.",
            data={"thread": "renewal-follow-up", "local_status": "sent"},
        ),
        WorkflowEvent(
            ts="2026-09-08T08:59:14.410Z",
            kind=EventKind.planned_action,
            source="follow-up-agent",
            summary="Agent schedules next task: wait three business days for client response.",
            data={"next_check": "2026-09-11T09:00:00Z", "assumed_delivery": True},
        ),
        WorkflowEvent(
            ts="2026-09-08T09:00:03.812Z",
            kind=EventKind.provider_response,
            source="email-provider",
            summary="Provider rejects outbound email after policy scan.",
            data={"provider_status": "rejected", "reason": "policy_scan_failed"},
        ),
        WorkflowEvent(
            ts="2026-09-08T09:02:20.240Z",
            kind=EventKind.external_observation,
            source="email-provider",
            summary="Thread has no delivered message and no client-visible update.",
            data={"delivered": False, "thread_status": "unchanged"},
        ),
    ]
    return Incident(
        id="inbox-undelivered-followup",
        title="Follow-up agent believed rejected email was sent",
        domain="Client communications",
        status="needs_approval",
        severity=Severity.medium,
        user="Small business owner",
        summary=(
            "A follow-up workflow moved on as if a message was delivered, but the provider "
            "rejected it and the client never saw the update."
        ),
        events=events,
    )


def all_incidents() -> list[Incident]:
    return [tradeops_incident(), inbox_incident()]


def get_incident(incident_id: str) -> Incident | None:
    for incident in all_incidents():
        if incident.id == incident_id:
            return incident
    return None


def adapter_examples() -> list[dict[str, str]]:
    return [
        {
            "name": "Inbox Agent",
            "belief": "Follow-up email was sent to the client.",
            "reality": "Email provider rejected delivery after a policy check.",
            "escalation": "Ask before resending from an alternate account.",
        },
        {
            "name": "Volunteer Scheduler",
            "belief": "Saturday morning shift has three confirmed volunteers.",
            "reality": "Calendar has one accepted invite and two pending invites.",
            "escalation": "Ask coordinator before paging backup volunteers.",
        },
    ]
