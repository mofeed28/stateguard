"""One authorized self-email; durable claim prevents automatic resend after uncertainty.

The acknowledgment loss is injected locally AFTER a real send call. Message-ID is
an evidence correlation key, not a Gmail idempotency guarantee. Never delete the
claim to retry an uncertain send. --check-only can safely recheck Gmail evidence.
"""
import argparse
import base64
import json
import os
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
CLAIM = ROOT / ".secrets" / "gmail-demo-attempt.json"


def claim_attempt(path, account):
    attempt = {"message_id": f"stateguard-{uuid4().hex}@stateguard.local",
               "account": account, "worker_belief": "unknown", "send_claimed": True,
               "created_at": datetime.now(timezone.utc).isoformat(),
               "fault": "Discard acknowledgment after real Gmail send; controlled injection"}
    try:
        with path.open("x", encoding="utf-8") as handle:
            json.dump(attempt, handle)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError:
        return json.loads(path.read_text(encoding="utf-8")), False
    return attempt, True


from stateguard.gmail_evidence import check_evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--send-approved-self-test", action="store_true")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    creds = Credentials.from_authorized_user_file(str(ROOT / ".secrets" / "gmail-token.json"))
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    account = service.users().getProfile(userId="me").execute(num_retries=0)["emailAddress"]
    if args.send_approved_self_test and not args.check_only:
        attempt, claimed = claim_attempt(CLAIM, account)
    else:
        attempt = json.loads(CLAIM.read_text(encoding="utf-8"))
        claimed = False
    if attempt["account"] != account:
        raise RuntimeError("The authorized Gmail account changed. Stop before sending or checking.")
    if claimed:
        message = EmailMessage()
        message["From"] = message["To"] = account
        message["Subject"] = "StateGuard delivery test"
        message["Message-ID"] = "<" + attempt["message_id"] + ">"
        message.set_content("Controlled StateGuard demo. No action needed.")
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
        service.users().messages().send(userId="me", body={"raw": raw}).execute(num_retries=0)
        # Intentionally do not use or persist Gmail's send response in worker state.
        print("Real Gmail send accepted; acknowledgment deliberately withheld from worker state.")
    evidence = check_evidence(service, attempt)
    report = {"mode": "real_gmail_self_email", "checked_at": datetime.now(timezone.utc).isoformat(),
              "worker_belief": "unknown", "send_claim_persisted": True,
              "retry_allowed": False, "retry_gate_reason": "A send attempt already exists; no automatic resend.",
              "fault_injection": attempt["fault"], "evidence": evidence,
              "status": "receipt_verified" if evidence["matching_messages"] == 1 and evidence["inbox_records"] == 1 and evidence["sent_records"] == 1 else "needs_review",
              "scope": "One controlled self-email. Sent and Inbox labels verify this mailbox only; no general delivery or exactly-once guarantee."}
    (ROOT / ".secrets" / "gmail-demo-evidence.json").write_text(json.dumps(report, indent=2),encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"success": False, "error_type": type(exc).__name__,
                          "next_step": "Do not resend. Resolve the error and run --check-only."}))
        raise SystemExit(1)
