import os
import base64
import json
import requests
from dotenv import load_dotenv
from schemas import RoutineCreate

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Groq's vision-capable model
MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

SYSTEM_PROMPT = """You extract weekly class schedules from images or text.

Output ONLY a JSON array of class objects. No markdown, no explanation.
Each object must have exactly these fields:
{
  "title": string (class name, 2-5 words),
  "day_of_week": integer (0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday, 5=Saturday, 6=Sunday),
  "start_time": string (HH:MM:SS, 24-hour),
  "end_time": string or null (HH:MM:SS),
  "location": string (room/building, empty string if unknown),
  "color": one of ["academic", "deadline", "social", "health", "work", "personal", "family", "other"]
}

Rules:
- Assign color based on course prefix:
  * CSE courses → "work"
  * EEE courses → "health"  
  * Math courses → "personal"
  * Hum courses → "family"
  * Any other course → "academic"
- If you see the same class multiple times per week, create one entry per day.
- Output ONLY the JSON array. Nothing else."""


def extract_routine_from_image(image_bytes: bytes, mime_type: str) -> list[RoutineCreate]:
    """Send an image to the LLM and get back a list of RoutineCreate objects."""
    b64 = base64.b64encode(image_bytes).decode("utf-8")

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
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{b64}"
                            },
                        },
                        {
                            "type": "text",
                            "text": "Extract all classes from this schedule image.",
                        },
                    ],
                },
            ],
            "temperature": 0.1,
        },
        timeout=60,
    )
    response.raise_for_status()
    raw = response.json()["choices"][0]["message"]["content"]

    # Strip markdown fences if the model adds them anyway
    clean = raw.strip()
    if clean.startswith("```"):
        clean = clean.split("```")[1]
        if clean.startswith("json"):
            clean = clean[4:]
    clean = clean.strip()

    data = json.loads(clean)
    return [RoutineCreate(**item) for item in data]


def extract_routine_from_text(text: str) -> list[RoutineCreate]:
    """Same extraction but from plain text instead of an image."""
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
        },
        timeout=60,
    )
    response.raise_for_status()
    raw = response.json()["choices"][0]["message"]["content"]

    clean = raw.strip()
    if clean.startswith("```"):
        clean = clean.split("```")[1]
        if clean.startswith("json"):
            clean = clean[4:]
    clean = clean.strip()

    data = json.loads(clean)
    return [RoutineCreate(**item) for item in data]