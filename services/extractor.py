from dotenv import load_dotenv
from datetime import date , time
import os
import json
import requests
from schemas import EventCreate

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"
CATEGORIES = [
    "academic", "deadline", "social", "health",
    "work", "personal", "family", "other"
]

SYSTEM_PROMPT = f"""You extract calendar events from natural language text.

Today's date is {date.today().isoformat()}.

You MUST output ONLY valid JSON matching this exact schema:
{{
  "title": string (short, 2-6 words),
  "description": string (1-2 sentences, can be empty string),
  "start_date": string (YYYY-MM-DD),
  "start_time": string (HH:MM:SS, 24-hour),
  "end_date": string or null (YYYY-MM-DD),
  "end_time": string or null (HH:MM:SS),
  "location": string (can be empty string),
  "priority": integer (1=urgent, 2=normal, 3=low),
  "color": one of {CATEGORIES},
  "source": "manual"
}}

Rules:
- If date is relative ("tomorrow", "next Tuesday"), resolve it to YYYY-MM-DD using today's date above.
- If time isn't given, assume 09:00:00.
- If end_time isn't given, set it and end_date to null.
- Pick the most fitting category for "color".
- Output ONLY the JSON object. No markdown, no explanation, no surrounding text."""

def extract_event(text: str) -> EventCreate:
    """Call the LLM with the user's text and parse the response into an EventCreate."""

    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set in .env file")

    response = requests.post(
        GROQ_URL,
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        },
        timeout=30,
    )

    response.raise_for_status()
    raw_content = response.json()["choices"][0]["message"]["content"]

    data = json.loads(raw_content)
    return EventCreate(**data)