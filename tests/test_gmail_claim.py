"""Offline tests for the durable single-send claim."""
import importlib.util
from pathlib import Path
import pytest
spec = importlib.util.spec_from_file_location("gmail_demo", Path(__file__).resolve().parents[1] / "scripts/gmail_delivery_demo.py")
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)


def test_existing_claim_cannot_authorize_a_second_send(tmp_path):
    path = tmp_path / "claim.json"
    first, allowed = demo.claim_attempt(path, "test@example.invalid")
    assert allowed
    again, allowed = demo.claim_attempt(path, "test@example.invalid")
    assert not allowed
    assert first == again
    assert again["worker_belief"] == "unknown"


def test_incomplete_claim_fails_closed(tmp_path):
    path = tmp_path / "claim.json"
    path.write_text("")
    with pytest.raises(ValueError):
        demo.claim_attempt(path, "test@example.invalid")
