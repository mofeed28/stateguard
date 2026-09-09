from fastapi.testclient import TestClient

from stateguard.app import app


client = TestClient(app)


def test_replay_detects_high_risk_mismatches():
    response = client.get("/api/incidents/tradeops-ambiguous-cancel-double-entry/replay")
    assert response.status_code == 200
    payload = response.json()

    assert payload["incident"]["severity"] == "high"
    assert len(payload["mismatches"]) == 2
    assert [step["agent"] for step in payload["execution_trace"]] == [
        "Supervisor",
        "Timeline Investigator",
        "Reality Reconciler",
        "Risk Sentinel",
        "Human Approval Agent",
        "Handoff Writer",
    ]
    assert payload["decision"]["requires_approval"] is True
    assert "Pause new entry placement" in payload["decision"]["recommended_action"]


def test_handoff_is_sanitized():
    response = client.get("/api/incidents/tradeops-ambiguous-cancel-double-entry/replay")
    handoff = response.json()["sanitized_handoff"].lower()

    assert "secret" in handoff
    assert "api_key" not in handoff
    assert "password" not in handoff
    assert "/home/" not in handoff


def test_adapter_examples_show_extensibility():
    response = client.get("/api/adapters")
    assert response.status_code == 200
    examples = response.json()

    assert {example["name"] for example in examples} == {
        "Inbox Agent",
        "Volunteer Scheduler",
    }


def test_inbox_replay_proves_non_finance_adapter():
    response = client.get("/api/incidents/inbox-undelivered-followup/replay")
    assert response.status_code == 200
    payload = response.json()

    assert payload["incident"]["domain"] == "Client communications"
    assert payload["incident"]["severity"] == "medium"
    assert payload["mismatches"][0]["title"].startswith("Workflow belief")


def test_scheduler_replay_proves_human_operations_adapter():
    response = client.get("/api/incidents/scheduler-unconfirmed-volunteer-coverage/replay")
    assert response.status_code == 200
    payload = response.json()

    assert payload["incident"]["domain"] == "Operations scheduling"
    assert payload["incident"]["severity"] == "medium"
    assert len(payload["mismatches"]) == 2
    assert "backup volunteer outreach" in payload["decision"]["recommended_action"]


def test_strands_tools_endpoint_lists_decorated_tools():
    response = client.get("/api/strands-tools")
    assert response.status_code == 200
    names = {tool["name"] for tool in response.json()}

    assert "load_incident_events" in names
    assert "detect_state_mismatches" in names
    assert "classify_automation_risk" in names
    assert "generate_sanitized_handoff" in names


def test_structured_output_is_validated_for_demo():
    response = client.get(
        "/api/incidents/tradeops-ambiguous-cancel-double-entry/structured-output"
    )
    assert response.status_code == 200
    payload = response.json()

    assert payload["incident_id"] == "tradeops-ambiguous-cancel-double-entry"
    assert payload["severity"] == "high"
    assert payload["mismatch_count"] == 2
    assert payload["approval_required"] is True
    assert payload["confidence"] >= 0.9


def test_observability_events_show_production_trace():
    response = client.get(
        "/api/incidents/inbox-undelivered-followup/observability"
    )
    assert response.status_code == 200
    events = response.json()

    assert {event["event"] for event in events} >= {
        "incident.events.loaded",
        "belief_reality.mismatch_detected",
        "autonomous_action.blocked",
        "operator_handoff.ready",
    }


def test_custom_mismatch_simulator_returns_structured_decision():
    response = client.post(
        "/api/simulate-mismatch",
        json={
            "domain": "Invoice collection",
            "agent_belief": "Agent believes invoice #104 was paid and marks the account as settled.",
            "external_reality": "Bank API shows no settled payment and the invoice remains unpaid.",
            "risky_action": "Close the collection task and stop follow-up reminders.",
        },
    )
    assert response.status_code == 200
    payload = response.json()

    assert payload["result"]["incident"]["id"] == "custom-simulated-mismatch"
    assert payload["structured_output"]["approval_required"] is True
    assert payload["structured_output"]["mismatch_count"] == 1
    assert "Without StateGuard" in payload["without_stateguard"]
    assert "With StateGuard" in payload["with_stateguard"]


def test_live_mismatch_endpoint_falls_back_when_disabled():
    response = client.post(
        "/api/simulate-mismatch/live",
        json={
            "domain": "Invoice collection",
            "agent_belief": "Agent believes invoice #104 was paid and marks the account as settled.",
            "external_reality": "Bank API shows no settled payment and the invoice remains unpaid.",
            "risky_action": "Close the collection task and stop follow-up reminders.",
        },
    )
    assert response.status_code == 200
    payload = response.json()

    assert payload["live_mode"] is False
    assert "disabled" in payload["live_error"]
    assert payload["structured_output"]["approval_required"] is True


def test_live_mismatch_endpoint_requires_key_when_live_enabled(monkeypatch):
    monkeypatch.setenv("STATEGUARD_USE_STRANDS_LLM", "1")
    monkeypatch.setenv("STATEGUARD_LIVE_DEMO_KEY", "demo-secret")

    response = client.post(
        "/api/simulate-mismatch/live",
        json={
            "domain": "Invoice collection",
            "agent_belief": "Agent believes invoice #104 was paid and marks the account as settled.",
            "external_reality": "Bank API shows no settled payment and the invoice remains unpaid.",
            "risky_action": "Close the collection task and stop follow-up reminders.",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "live_demo_key_required"


def test_live_mismatch_endpoint_rejects_before_body_validation(monkeypatch):
    monkeypatch.setenv("STATEGUARD_USE_STRANDS_LLM", "1")
    monkeypatch.setenv("STATEGUARD_LIVE_DEMO_KEY", "demo-secret")

    response = client.post(
        "/api/simulate-mismatch/live",
        json={
            "domain": "x",
            "agent_belief": "short",
            "external_reality": "short",
            "risky_action": "short",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "live_demo_key_required"


def test_live_mismatch_endpoint_rejects_cross_origin_posts(monkeypatch):
    monkeypatch.setenv("STATEGUARD_USE_STRANDS_LLM", "1")
    monkeypatch.setenv("STATEGUARD_LIVE_DEMO_KEY", "demo-secret")

    response = client.post(
        "/api/simulate-mismatch/live",
        headers={
            "Origin": "https://evil.example",
            "X-StateGuard-Live-Key": "demo-secret",
        },
        json={
            "domain": "Invoice collection",
            "agent_belief": "Agent believes invoice #104 was paid and marks the account as settled.",
            "external_reality": "Bank API shows no settled payment and the invoice remains unpaid.",
            "risky_action": "Close the collection task and stop follow-up reminders.",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "live_origin_not_allowed"
