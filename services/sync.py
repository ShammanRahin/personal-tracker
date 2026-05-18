from sqlalchemy.orm import Session
from services.gmail import fetch_recent_emails
from services.extractor import extract_event
import crud.events as crud_events
from services.agent import run_agent


def sync_gmail(db: Session, limit: int = 10) -> dict:
    """Fetch recent emails, let the agent decide what to do with each."""
    emails = fetch_recent_emails(limit=limit)
    results = []

    for email in emails:
        text = f"Subject: {email['subject']}\n\n{email['snippet']}"

        # Fetch fresh events each time — earlier emails may have changed things
        events = crud_events.get_events(db)

        try:
            reply = run_agent(db, text, events)
        except Exception as e:
            reply = f"Error: {str(e)}"

        results.append({"subject": email["subject"], "agent_reply": reply})

    return {"processed": len(results), "results": results}