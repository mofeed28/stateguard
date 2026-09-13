from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from stateguard.app import app
from stateguard import workflow


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("STATEGUARD_DB_PATH", str(tmp_path / "runs.sqlite3"))
    monkeypatch.delenv("STATEGUARD_USE_STRANDS_LLM", raising=False)
    return TestClient(app)


def start(client, scenario="accepted_timeout"):
    response = client.post("/api/workflows", json={"scenario": scenario})
    assert response.status_code == 200
    return response.json()


def test_duplicate_prevented_and_approval_verifies_recovery(client):
    run = start(client)
    path = f"/api/workflows/{run['id']}"
    blocked = client.post(path + "/tick").json()
    assert blocked["status"] == "needs_approval"
    assert blocked["deliveries"] == 1
    recovered = client.post(path + "/approve", json={"version": blocked["version"]}).json()
    assert recovered["status"] == "completed"
    assert recovered["belief"] == recovered["provider"] == "delivered"
    assert recovered["deliveries"] == 1
    assert client.get(path).json() == recovered
    assert client.post(path + "/approve", json={"version": blocked["version"]}).json() == recovered
    assert client.post(path + "/tick").json() == recovered


def test_healthy_workflow_needs_no_human_and_concurrent_ticks_send_once(client):
    run = start(client, "healthy")
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _: workflow.tick(run["id"]), range(16)))
    assert all(r["status"] == "completed" and r["deliveries"] == 1 for r in results)
    assert all(not any(e["event"] == "approval.recorded" for e in r["events"]) for r in results)


@pytest.mark.parametrize("scenario", ["delayed", "unavailable"])
def test_uncertainty_waits_then_rechecks_provider(client, scenario):
    run = start(client, scenario)
    path = f"/api/workflows/{run['id']}"
    waiting = client.post(path + "/tick").json()
    assert waiting["status"] == "waiting" and waiting["deliveries"] == 0
    assert client.post(path + "/approve", json={"version": waiting["version"]}).status_code == 409
    client.post(path + "/provider", json={"state": "not_sent"})
    done = client.post(path + "/tick").json()
    assert done["status"] == "completed" and done["deliveries"] == 1


def test_stale_approval_cannot_override_new_provider_evidence(client):
    run = start(client)
    path = f"/api/workflows/{run['id']}"
    blocked = client.post(path + "/tick").json()
    client.post(path + "/provider", json={"state": "unavailable"})
    assert client.post(path + "/approve", json={"version": blocked["version"]}).status_code == 409
    assert client.post(path + "/tick").json()["status"] == "waiting"
    assert client.get(path).json()["deliveries"] == 1


def test_runs_isolated_and_missing_run_rejected(client):
    first, second = start(client), start(client, "healthy")
    workflow.tick(first["id"])
    assert workflow.get_run(second["id"])["status"] == "ready"
    assert client.post("/api/workflows/missing/approve", json={"version": 0}).status_code == 404
    assert client.post("/api/incidents/missing/approve").status_code == 404


def test_background_worker_runs_healthy_and_only_surfaces_confirmed_conflict(client):
    from stateguard.worker import run_once
    healthy, conflict, pending = start(client, "healthy"), start(client), start(client, "delayed")
    run_once()
    assert workflow.get_run(healthy["id"])["status"] == "completed"
    assert workflow.get_run(conflict["id"])["status"] == "needs_approval"
    waiting = workflow.get_run(pending["id"])
    assert waiting["status"] == "waiting"
    run_once()
    assert workflow.get_run(pending["id"]) == waiting  # Quiet while unchanged.
    workflow.update_provider(pending["id"], "delivered")
    run_once()
    assert workflow.get_run(pending["id"])["status"] == "needs_approval"


def test_disabled_live_analysis_is_explicit_failure_not_fake_success(client):
    run = start(client)
    assert client.post(f"/api/workflows/{run['id']}/investigate").status_code == 503
    assert workflow.get_run(run["id"])["analysis"] is None


def test_live_endpoint_requires_key(client, monkeypatch):
    run = start(client)
    monkeypatch.setenv("STATEGUARD_USE_STRANDS_LLM", "1")
    monkeypatch.setenv("STATEGUARD_LIVE_DEMO_KEY", "test-key")
    assert client.post(f"/api/workflows/{run['id']}/investigate").status_code == 403


def test_model_quota_error_is_explained_without_fake_analysis(client, monkeypatch):
    from strands.types.exceptions import ModelThrottledException
    run = start(client)
    def throttled(_):
        raise ModelThrottledException("Too many tokens per day")
    monkeypatch.setattr(workflow, "investigate_run", throttled)
    response = client.post(f"/api/workflows/{run['id']}/investigate")
    assert response.status_code == 429
    assert "usage limit" in response.json()["detail"]
    assert workflow.get_run(run["id"])["analysis"] is None


def test_live_agent_tools_read_current_evidence_and_record_actual_calls(client, monkeypatch):
    import strands
    from types import SimpleNamespace

    run = start(client)
    monkeypatch.setenv("STATEGUARD_USE_STRANDS_LLM", "1")

    class FakeAgent:
        def __init__(self, **kwargs):
            self.tools = kwargs["tools"]

        def __call__(self, *args, **kwargs):
            history, provider = (tool() for tool in self.tools)
            assert history["belief"] == "not_sent"
            assert provider["provider"] == "delivered"
            return SimpleNamespace(structured_output=workflow.Analysis(summary="Provider delivered after worker timeout.", evidence=["One provider delivery"], recommendation="reconcile"))

    monkeypatch.setattr(strands, "Agent", FakeAgent)
    from strands.models import bedrock
    monkeypatch.setattr(bedrock, "BedrockModel", lambda **kwargs: None)
    result = workflow.investigate_run(run["id"])
    assert len(result["analysis"]["trace"]) == 2
    assert result["status"] == "ready"  # Analysis never authorizes execution.


def test_matching_text_does_not_invent_mismatch_and_secrets_redacted(client):
    payload = {"domain": "Email retry", "agent_belief": "Message was delivered successfully", "external_reality": "Message was delivered successfully", "risky_action": "Mark the email task completed"}
    output = client.post("/api/simulate-mismatch", json=payload).json()
    assert output["structured_output"]["mismatch_count"] == 0
    assert output["structured_output"]["approval_required"] is False
    payload["agent_belief"] = "api_key=FAKE_TEST_VALUE_ONLY owner@example.com"
    output = client.post("/api/simulate-mismatch", json=payload).json()
    handoff = output["result"]["sanitized_handoff"]
    assert "FAKE_TEST_VALUE_ONLY" not in handoff
    assert "owner@example.com" not in handoff
    assert "[REDACTED]" in handoff
