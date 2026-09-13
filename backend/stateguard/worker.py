"""Standalone background worker for a single-host sandbox deployment."""
import argparse
import logging
import os
import time

from .workflow import pending_runs, tick, investigate_run

log = logging.getLogger("stateguard.worker")


def run_once():
    for run_id in pending_runs():
        try:
            run = tick(run_id)
            if run["status"] == "needs_approval" and os.getenv("STATEGUARD_USE_STRANDS_LLM") == "1":
                investigate_run(run_id)
        except Exception as exc:
            # Preserve the gate and continue processing other workflows.
            log.warning("Workflow %s requires attention (%s)", run_id, type(exc).__name__)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=float, default=5)
    args = parser.parse_args()
    if args.interval < 1:
        parser.error("interval must be at least one second")
    logging.basicConfig(level=logging.INFO)
    while True:
        run_once()
        if args.once:
            return
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
