import pytest
from stateguard.model import create_model


def test_openai_missing_key_fails_before_network(monkeypatch):
    monkeypatch.setenv("STATEGUARD_MODEL_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY is missing"):
        create_model()


def test_unknown_provider_does_not_silently_use_bedrock(monkeypatch):
    monkeypatch.setenv("STATEGUARD_MODEL_PROVIDER", "typo")
    with pytest.raises(RuntimeError, match="must be openai or bedrock"):
        create_model()
