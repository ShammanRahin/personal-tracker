import os
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import json

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"



def get_gmail_service():
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    else:
        token_json_str = os.getenv("GOOGLE_TOKEN_JSON")
        if token_json_str:
            creds = Credentials.from_authorized_user_info(
                json.loads(token_json_str), SCOPES
            )

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise RuntimeError(
                "No valid Google credentials on server. "
                "Re-authorize locally and update GOOGLE_TOKEN_JSON."
            )

    return build("gmail", "v1", credentials=creds)


def _get_header(headers: list, name: str) -> str:
    """Pull a single header value (e.g. 'Subject') out of the headers list."""
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def _get_body(payload: dict) -> str:
    """Extract the plain-text body from a message payload."""
    # Simple case: body is right here
    if payload.get("body", {}).get("data"):
        return _decode(payload["body"]["data"])

    # Multipart case: dig through the parts for a text/plain section
    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain":
            data = part.get("body", {}).get("data")
            if data:
                return _decode(data)
        # Nested parts (some emails nest parts inside parts)
        if part.get("parts"):
            nested = _get_body(part)
            if nested:
                return nested
    return ""


def _decode(data: str) -> str:
    """Decode Gmail's base64url-encoded body data into a normal string."""
    return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")


def fetch_recent_emails(limit: int = 10, query: str = "newer_than:7d") -> list:
    """Fetch recent emails as a list of clean dicts."""
    service = get_gmail_service()

    result = service.users().messages().list(
        userId="me", q=query, maxResults=limit
    ).execute()
    messages = result.get("messages", [])

    emails = []
    for msg in messages:
        full = service.users().messages().get(
            userId="me", id=msg["id"]
        ).execute()

        payload = full["payload"]
        headers = payload.get("headers", [])

        emails.append({
            "id": msg["id"],
            "subject": _get_header(headers, "Subject"),
            "sender": _get_header(headers, "From"),
            "snippet": full.get("snippet", ""),
            "body": _get_body(payload),
        })

    return emails