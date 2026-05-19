import os
import json
from datetime import datetime, timezone
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.me.readonly",
    "https://www.googleapis.com/auth/classroom.announcements.readonly",
]
TOKEN_FILE = "token.json"


def get_classroom_service():
    """Auth with Google and return a Classroom service object."""
    creds = None

    token_json_str = os.getenv("GOOGLE_TOKEN_JSON")
    if token_json_str:
        creds = Credentials.from_authorized_user_info(
            json.loads(token_json_str), SCOPES
        )
    elif os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise RuntimeError(
                "No valid Google credentials. "
                "Re-authorize locally and update GOOGLE_TOKEN_JSON."
            )

    return build("classroom", "v1", credentials=creds)


def fetch_courses() -> list:
    """Return all active enrolled courses."""
    service = get_classroom_service()
    courses = []
    page_token = None

    while True:
        result = service.courses().list(
            studentId="me",
            courseStates=["ACTIVE"],
            pageToken=page_token,
        ).execute()

        courses.extend(result.get("courses", []))
        page_token = result.get("nextPageToken")
        if not page_token:
            break

    return courses


def fetch_assignments(course_id: str, limit: int = 20) -> list:
    """Return upcoming coursework for one course."""
    service = get_classroom_service()
    result = service.courses().courseWork().list(
        courseId=course_id,
        orderBy="dueDate asc",
        pageSize=limit,
        courseWorkStates=["PUBLISHED"],
    ).execute()

    items = result.get("courseWork", [])
    assignments = []

    for item in items:
        due = item.get("dueDate")
        due_time = item.get("dueTime")

        if not due:
            continue

        # Build ISO date string
        due_date = f"{due['year']}-{str(due['month']).zfill(2)}-{str(due['day']).zfill(2)}"

        if due_time:
            due_hour = str(due_time.get("hours", 23)).zfill(2)
            due_minute = str(due_time.get("minutes", 59)).zfill(2)
            due_time_str = f"{due_hour}:{due_minute}:00"
        else:
            due_time_str = "23:59:00"

        assignments.append({
            "id": item["id"],
            "course_id": course_id,
            "title": item.get("title", "Assignment"),
            "description": item.get("description", ""),
            "due_date": due_date,
            "due_time": due_time_str,
            "link": item.get("alternateLink", ""),
        })

    return assignments


def fetch_announcements(course_id: str, limit: int = 10) -> list:
    """Return recent announcements for one course."""
    service = get_classroom_service()
    try:
        result = service.courses().announcements().list(
            courseId=course_id,
            announcementStates=["PUBLISHED"],
            pageSize=limit,
            orderBy="updateTime desc",
        ).execute()
    except Exception:
        return []

    items = result.get("announcements", [])
    announcements = []

    for item in items:
        announcements.append({
            "id": item["id"],
            "course_id": course_id,
            "text": item.get("text", ""),
            "update_time": item.get("updateTime", ""),
        })

    return announcements