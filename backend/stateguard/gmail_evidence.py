"""Read only evidence for the one authorized Gmail self-test."""
from datetime import datetime

def check_evidence(service, attempt):
    records = []
    query = "rfc822msgid:" + attempt["message_id"]
    probe = service.users().messages().list(userId="me", q=query,
        includeSpamTrash=True, maxResults=1).execute(num_retries=0)
    correlation = "message_id"
    if not probe.get("messages"):
        start = int(datetime.fromisoformat(attempt["created_at"]).timestamp())
        query = (f'in:anywhere subject:"StateGuard delivery test" '
                 f'from:{attempt["account"]} to:{attempt["account"]} '
                 f'after:{start - 5} before:{start + 120}')
        correlation = "subject_account_send_window; Gmail may rewrite Message-ID"
    page = None
    while True:
        response = service.users().messages().list(userId="me",
            q=query, includeSpamTrash=True,
            maxResults=100, pageToken=page).execute(num_retries=0)
        for item in response.get("messages", []):
            msg = service.users().messages().get(userId="me", id=item["id"],
                format="metadata", metadataHeaders=["Message-ID", "Subject"]).execute(num_retries=0)
            headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
            if headers.get("subject") != "StateGuard delivery test":
                continue
            records.append({"id": msg["id"], "labels": msg.get("labelIds", [])})
        page = response.get("nextPageToken")
        if not page:
            break
    return {"correlation": correlation, "matching_messages": len(records),
            "sent_records": sum("SENT" in m["labels"] for m in records),
            "inbox_records": sum("INBOX" in m["labels"] for m in records),
            "records": records}
