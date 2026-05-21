from sqlalchemy.orm import Session
from services.classroom import fetch_courses, fetch_assignments, fetch_announcements
from services.agent import run_agent
from crud import events as crud_events
from schemas import EventCreate
from datetime import date


def sync_classroom(db: Session, assignment_limit: int = 20) -> dict:
    """
    Pull all assignments and announcements from Classroom,
    run each through the agent, save results.
    """
    courses = fetch_courses()
    if not courses:
        return {"courses_found": 0, "processed": 0, "results": []}

    all_results = []

    for course in courses:
        course_id = course["id"]
        course_name = course.get("name", "Unknown Course")

        # ── Assignments ──────────────────────────────────────────
        assignments = fetch_assignments(course_id, limit=assignment_limit)
        for a in assignments:
            sid = f"classroom:{a['id']}"
            if crud_events.get_event_by_source_id(db, sid):
                continue

            text = (
                f"Assignment due: {a['title']} "
                f"for {course_name} "
                f"on {a['due_date']} at {a['due_time']}."
                f" [source_id: {sid}]"
            )
            if a["description"]:
                text += f" Details: {a['description'][:150]}"

            events = crud_events.get_events(db, lim=50)
            try:
                reply = run_agent(db, text, events)
            except Exception as e:
                reply = f"Error: {str(e)}"

            all_results.append({
                "type": "assignment",
                "course": course_name,
                "title": a["title"],
                "agent_reply": reply,
            })

        # ── Announcements ────────────────────────────────────────
        announcements = fetch_announcements(course_id)
        for ann in announcements:
            if not ann["text"].strip():
                continue

            sid = f"classroom_ann:{ann['id']}"
            if crud_events.get_event_by_source_id(db, sid):
                continue

            text = f"Classroom announcement from {course_name}: {ann['text'][:200]} [source_id: {sid}]"
            events = crud_events.get_events(db, lim=50)
            try:
                reply = run_agent(db, text, events)
            except Exception as e:
                reply = f"Error: {str(e)}"

            all_results.append({
                "type": "announcement",
                "course": course_name,
                "text": ann["text"][:100],
                "agent_reply": reply,
            })

    return {
        "courses_found": len(courses),
        "processed": len(all_results),
        "results": all_results,
    }
