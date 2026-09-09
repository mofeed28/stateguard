from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
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
def simulate_mismatch_live(payload: CustomMismatchRequest) -> CustomMismatchResponse:
    return simulate_live_mismatch(payload)


@app.get("/api/adapters")
def adapters() -> list[dict[str, str]]:
    return adapter_examples()


app.mount("/assets", StaticFiles(directory=FRONTEND_DIR), name="assets")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(f"{FRONTEND_DIR}/index.html")


handler = Mangum(app)
