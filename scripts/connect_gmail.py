"""Authorize the local Gmail demo. Does not send mail or read message contents."""
from pathlib import Path
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parents[1]
SCOPES = ["https://www.googleapis.com/auth/gmail.send", "https://www.googleapis.com/auth/gmail.readonly"]


def main():
    client_path = ROOT / ".secrets" / "gmail-client.json"
    token_path = ROOT / ".secrets" / "gmail-token.json"
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path))
        if not creds.has_scopes(SCOPES):
            creds = None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            config = json.loads(client_path.read_text(encoding="utf-8-sig"))
            if "installed" not in config:
                raise RuntimeError("Create a Desktop app OAuth client for this local demo.")
            flow = InstalledAppFlow.from_client_config(config, SCOPES)
            creds = flow.run_local_server(host="localhost", port=0, timeout_seconds=300,
                authorization_prompt_message="Opening Google sign-in in your browser. Authorize the dedicated demo account.",
                success_message="StateGuard Gmail authorization completed. You may close this tab.")
        token_path.write_text(creds.to_json(), encoding="utf-8")
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    profile = service.users().getProfile(userId="me").execute()
    print(json.dumps({"connected": True, "mailbox_verified": bool(profile.get("emailAddress")), "email_sent": False}))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"connected": False, "error_type": type(exc).__name__}))
        raise SystemExit(1)
