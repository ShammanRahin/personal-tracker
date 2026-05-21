from datetime import date, timedelta
from sqlalchemy.orm import Session
from schemas import EventCreate
from crud import events as crud_events
from models import Routinedb
from models import Eventdb

def _next_weekday(from_date: date, weekday: int) -> date:
    """Return the next occurrence of `weekday` (0=Mon) on or after `from_date`."""
    days_ahead = weekday - from_date.weekday()
    if days_ahead < 0:
        days_ahead += 7
    return from_date + timedelta(days=days_ahead)


def generate_upcoming_events(
    db: Session,
    routine: Routinedb,
    weeks_ahead: int = 12,
) -> int:
    """
    Generate the next `weeks_ahead` weeks of events for one routine.
    Skips dates that already have an event from this routine (idempotent).
    Returns the count of events created.
    """
    today = date.today()
    first_occurrence = _next_weekday(today, routine.day_of_week)

    created = 0
    for week in range(weeks_ahead):
        event_date = first_occurrence + timedelta(weeks=week)

        # Check if this slot already exists (avoid duplicates on re-run)
        existing = db.query(Eventdb).filter_by(
            routine_id=routine.id,
            start_date=event_date,
        ).first()
        if existing:
            continue

        event = EventCreate(
            title=routine.title,
            start_date=event_date,
            start_time=routine.start_time,
            end_time=routine.end_time,
            end_date=None,
            location=routine.location,
            color=routine.color,
            description="",
            priority=3,          # low priority — routine events are background
            source="routine",
            source_id=str(routine.id),
            routine_id=routine.id,
            is_routine=True,
        )
        crud_events.create_event(db, event)
        created += 1

    return created


def generate_all_active_routines(db: Session, weeks_ahead: int = 12) -> dict:
    """Run generate_upcoming_events for every active routine."""
    from crud import routines as crud_routines
    routines = crud_routines.get_routines(db, active_only=True)
    total = 0
    for r in routines:
        total += generate_upcoming_events(db, r, weeks_ahead)
    return {"routines_processed": len(routines), "events_created": total}