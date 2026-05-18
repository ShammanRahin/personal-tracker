from sqlalchemy.orm import Session
from services.gmail import fetch_recent_emails
from services.extractor import extract_event
import crud.events as crud_events


def sync_gmail(db: Session, limit: int = 10) -> dict:
    """Fetch recent emails, extract events from each, save to DB."""
    emails = fetch_recent_emails(limit=limit)

    created = []
    skipped = []

    for email in emails:
        # Build the text the LLM will read
        text = f"Subject: {email['subject']}\n\n{email['snippet']}"

        try:
            event_data = extract_event(text)
        except Exception as e:
            skipped.append({"subject": email["subject"], "reason": str(e)})
            continue

        # Tag the event with its origin
        event_data.source = "gmail"
        event_data.source_id = email["id"]

        new_event = crud_events.create_event(db, event_data)
        created.append(new_event.title)

    return {
        "created_count": len(created),
        "created": created,
        "skipped_count": len(skipped),
        "skipped": skipped,
    }