from __future__ import annotations

import hmac
import os
from urllib.parse import urlparse

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from mangum import Mangum

from .agents import (
    ROLES,
    build_structured_output,
    investigate,
    simulate_custom_mismatch,
    simulate_live_mismatch,
)
from .fixtures import adapter_examples, all_incidents, get_incident
from .models import CustomMismatchRequest, CustomMismatchResponse
from .tools import (
    classify_automation_risk,
    detect_state_mismatches,
    generate_sanitized_handoff,
    load_incident_events,
)

app = FastAPI(title="StateGuard", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = "frontend"


def _live_mode_requires_key() -> bool:
    return os.getenv("STATEGUARD_USE_STRANDS_LLM") == "1"


def _live_key_is_valid(candidate: str | None) -> bool:
    live_key = os.getenv("STATEGUARD_LIVE_DEMO_KEY")
    return bool(live_key and candidate and hmac.compare_digest(candidate, live_key))


def _live_origin_is_allowed(request: Request) -> bool:
    origin = request.headers.get("origin")
    if not origin:
        return True

    parsed = urlparse(origin)
    expected_host = request.headers.get("host")
    return parsed.scheme == request.url.scheme and parsed.netloc == expected_host


@app.middleware("http")
async def protect_live_llm_endpoint(request: Request, call_next):
    if (
        _live_mode_requires_key()
        and request.url.path == "/api/simulate-mismatch/live"
        and request.method == "POST"
    ):
        if not _live_origin_is_allowed(request):
            return JSONResponse(
                status_code=403, content={"detail": "live_origin_not_allowed"}
            )
        if not _live_key_is_valid(request.headers.get("x-stateguard-live-key")):
            return JSONResponse(
                status_code=403, content={"detail": "live_demo_key_required"}
            )
    return await call_next(request)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "stateguard"}


@app.get("/api/roles")
def roles() -> list[dict[str, str]]:
    return [{"name": role.name, "role": role.role, "prompt": role.system_prompt} for role in ROLES]


@app.get("/api/strands-tools")
def strands_tools() -> list[dict[str, str]]:
    tools = [
        load_incident_events,
        detect_state_mismatches,
        classify_automation_risk,
        generate_sanitized_handoff,
    ]
    return [
        {
            "name": getattr(item, "__name__", item.__class__.__name__),
            "description": (getattr(item, "__doc__", "") or "").strip().split("\n")[0],
        }
        for item in tools
    ]


@app.get("/api/incidents")
def incidents() -> list[dict[str, str]]:
    return [
        {
            "id": incident.id,
            "title": incident.title,
            "domain": incident.domain,
            "severity": incident.severity,
            "status": incident.status,
            "summary": incident.summary,
        }
        for incident in all_incidents()
    ]


@app.get("/api/incidents/{incident_id}/replay")
def replay(incident_id: str):
    incident = get_incident(incident_id)
    if not incident:
        return {"error": "incident_not_found"}
    return investigate(incident)


@app.get("/api/incidents/{incident_id}/structured-output")
def structured_output(incident_id: str):
    incident = get_incident(incident_id)
    if not incident:
        return {"error": "incident_not_found"}
    return build_structured_output(investigate(incident))


@app.get("/api/incidents/{incident_id}/observability")
def observability(incident_id: str):
    incident = get_incident(incident_id)
    if not incident:
        return {"error": "incident_not_found"}
    return investigate(incident).observability_events


@app.post("/api/incidents/{incident_id}/approve")
def approve(incident_id: str) -> dict[str, str]:
    return {
        "incident_id": incident_id,
        "status": "approved_for_safe_maintenance",
        "next_step": "pause_new_actions_then_reconcile_external_state",
    }


@app.post("/api/simulate-mismatch")
def simulate_mismatch(payload: CustomMismatchRequest) -> CustomMismatchResponse:
    return simulate_custom_mismatch(payload)


@app.post("/api/simulate-mismatch/live")
def simulate_mismatch_live(
    payload: CustomMismatchRequest,
    x_stateguard_live_key: str | None = Header(default=None),
) -> CustomMismatchResponse:
    if _live_mode_requires_key():
        live_key = os.getenv("STATEGUARD_LIVE_DEMO_KEY")
        if not live_key:
            raise HTTPException(status_code=403, detail="live_demo_key_not_configured")
        if not x_stateguard_live_key or not _live_key_is_valid(x_stateguard_live_key):
            raise HTTPException(status_code=403, detail="live_demo_key_required")
    return simulate_live_mismatch(payload)


@app.get("/api/adapters")
def adapters() -> list[dict[str, str]]:
    return adapter_examples()


app.mount("/assets", StaticFiles(directory=FRONTEND_DIR), name="assets")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(f"{FRONTEND_DIR}/index.html")


@app.get("/architecture")
def architecture() -> FileResponse:
    return FileResponse("docs/architecture-diagram.html")


handler = Mangum(app)
