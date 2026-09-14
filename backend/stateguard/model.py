"""Explicit Strands provider selection with bounded requests."""
import os
from .runtime_config import value


def create_model():
    provider = os.getenv("STATEGUARD_MODEL_PROVIDER", "bedrock").lower()
    if provider == "openai":
        from strands.models.openai import OpenAIModel
        if not value("OPENAI_API_KEY", "").strip():
            raise RuntimeError("OPENAI_API_KEY is missing. Add it to the project .env file.")
        model_id = os.getenv("STATEGUARD_OPENAI_MODEL_ID", "gpt-5-mini")
        model = OpenAIModel(model_id=model_id,
            client_args={"api_key": value("OPENAI_API_KEY"), "max_retries": 0, "timeout": 45.0},
            params={"max_completion_tokens": 4000, "reasoning_effort": "low"})
    elif provider == "bedrock":
        from strands.models.bedrock import BedrockModel
        from botocore.config import Config
        model_id = os.getenv("STATEGUARD_BEDROCK_MODEL_ID", "amazon.nova-micro-v1:0")
        model = BedrockModel(model_id=model_id, region_name=os.getenv("AWS_REGION", "us-east-1"),
            temperature=0, max_tokens=1200,
            boto_client_config=Config(connect_timeout=3, read_timeout=20, retries={"max_attempts": 1}))
    else:
        raise RuntimeError("STATEGUARD_MODEL_PROVIDER must be openai or bedrock.")
    return model, model_id, provider
