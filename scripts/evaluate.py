"""Reproducible sandbox evaluation. No cloud access, LLM, or real email."""
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from stateguard import workflow


def evaluate():
    rows = []
    for scenario in ("accepted_timeout", "healthy", "delayed", "unavailable"):
        initial = workflow.create_run(scenario)
        guarded = workflow.tick(initial["id"])
        # Explicit comparison baseline: retry once on the worker's not_sent flag,
        # without querying the provider. A delivered message becomes a duplicate.
        baseline_duplicate = initial["provider"] == "delivered"
        rows.append({"scenario": scenario, "initial_deliveries": initial["deliveries"],
                     "naive_retry_would_duplicate": baseline_duplicate,
                     "guarded_deliveries": guarded["deliveries"], "guarded_status": guarded["status"],
                     "human_approval_requested": guarded["status"] == "needs_approval"})
    return {"scope": "Four constructed sandbox scenarios; no real-world effectiveness or LLM accuracy claim.",
            "baseline": "Retry once from local not_sent belief; duplicate prediction only.",
            "results": rows, "confirmed_duplicate_cases_prevented": "1/1",
            "healthy_cases_incorrectly_blocked": "0/1", "uncertain_cases_held_without_approval": "2/2",
            "live_model_evaluated": False}


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="stateguard-eval-") as directory:
        os.environ["STATEGUARD_DB_PATH"] = str(Path(directory) / "evaluation.sqlite3")
        report = evaluate()
        # Counts above are checked against observed results before publication.
        assert [r["guarded_status"] for r in report["results"]] == ["needs_approval", "completed", "waiting", "waiting"]
        assert [r["guarded_deliveries"] for r in report["results"]] == [1, 1, 0, 0]
        output = Path(__file__).resolve().parents[1] / "docs" / "evaluation.json"
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
