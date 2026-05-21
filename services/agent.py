import json
from sqlalchemy.orm import Session
from crud import events as crud_events
from schemas import EventCreate, EventUpdate
import os
import requests
from datetime import date
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "openai/gpt-oss-120b"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_event",
            "description": "Create a new calendar event. Use when the text describes a new event, appointment, class, deadline, or meeting that isn't already tracked.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Short event title, 2-6 words"},
                    "description": {"type": "string", "description": "Short detail, can be empty"},
                    "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "start_time": {"type": "string", "description": "HH:MM:SS, 24-hour"},
                    "location": {"type": "string", "description": "Location, can be empty"},
                    "priority": {"type": ["integer", "string"], "description": "1=urgent, 2=normal, 3=low"},
                    "color": {
                        "type": "string",
                        "enum": ["academic", "deadline", "social", "health",
                                "work", "personal", "family", "other"],
                        "description": "Event category",
                    },
                    "source_id": {
                        "type": "string",
                        "description": "Stable external identifier for deduplication. Pass through unchanged if provided in the input text.",
                    },
                },
                "required": ["title", "start_date", "start_time", "priority", "color"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_event",
            "description": "Modify an existing event (change its time, date, location, etc). You must know the event's id first — call search_events if you don't.",
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "description": "The id of the event to update"},
                    "start_date": {"type": "string", "description": "New date, YYYY-MM-DD"},
                    "start_time": {"type": "string", "description": "New time, HH:MM:SS"},
                    "location": {"type": "string", "description": "New location"},
                    "title": {"type": "string", "description": "New title"},
                },
                "required": ["id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_event",
            "description": "Cancel or delete an event the user no longer needs. You must know the event's id first — call search_events if you don't.",
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "description": "The id of the event to delete"},
                },
                "required": ["id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_events",
            "description": "Find events by keyword. Use this to locate an event's id before updating or deleting it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Keyword to search for"},
                    "query_title": {
                        "type": "string",
                        "enum": ["title", "description", "location"],
                        "description": "Which field to search in",
                    },
                },
                "required": ["query", "query_title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "do_nothing",
            "description": "Use when the text is NOT about a calendar event — newsletters, ads, receipts, bank alerts, promotions, spam. Also use when no action is needed.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


def dispatch(db: Session, tool_name: str, arguments: dict) -> str:
    """Run the actual function the LLM asked for. Returns a string result."""

    if tool_name == "do_nothing":
        return "No action taken — not an event."

    if tool_name == "search_events":
        results = crud_events.search_events(
            db, query=arguments["query"], query_title=arguments["query_title"]
        )
        if not results:
            return "No matching events found."
        # Hand the LLM a compact summary it can read
        return json.dumps([
            {"id": e.id, "title": e.title, "start_date": str(e.start_date),
            "start_time": str(e.start_time)}
            for e in results
        ])

    if tool_name == "create_event":
        arguments.setdefault("description", "")
        arguments.setdefault("location", "")
        arguments.setdefault("end_time", None)
        arguments.setdefault("end_date", None)
        arguments.setdefault("source", "agent")
        if "priority" in arguments:
            arguments["priority"] = int(arguments["priority"])
        event = EventCreate(**arguments)
        new = crud_events.create_event(db, event)
        return f"Created event '{new.title}' (id {new.id})."
    if tool_name == "delete_event":
        event_id = int(arguments["id"])

        result = crud_events.delete_event(db, event_id)

        if not result:
            return f"No event with id {event_id} — nothing deleted."

        return f"Deleted event id {event_id}."
    if tool_name == "update_event":
        event_id = int(arguments.pop("id"))
        if "priority" in arguments:
            arguments["priority"] = int(arguments["priority"])
        update = EventUpdate(**arguments)
        result = crud_events.update_event(db, event_id, update)
        if result is None:
            return f"No event with id {event_id} — nothing updated."
        return f"Updated event id {event_id}."


def _call_groq(messages: list) -> dict:
    """One call to Groq with tools enabled. Returns the message object."""
    response = requests.post(
        GROQ_URL,
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={
            "model": MODEL,
            "messages": messages,
            "tools": TOOLS,
            "temperature": 0.1,
        },
        timeout=30,
    )
    if not response.ok:
        print("GROQ ERROR:", response.status_code, response.text)   # ← add this
    response.raise_for_status()
    return response.json()["choices"][0]["message"]


def run_agent(db: Session, user_text: str, existing_events: list) -> str:
    """Given some text + current events, let the LLM decide and act. Returns a final reply."""

    # Compact list of events so the LLM can match updates/cancellations
    events_summary = json.dumps([
        {"id": e.id, "title": e.title, "start_date": str(e.start_date),
        "start_time": str(e.start_time)}
        for e in existing_events
    ])

    system_prompt = f"""You manage a personal event tracker. Today is {date.today().isoformat()}. Today is a {date.today().strftime('%A')}.

When resolving relative dates:
- "next Monday" means the NEXT Monday after today, not the closest one
- "this Monday" means the Monday of the current week
- Always double-check: if today is Tuesday May 19, next Monday is May 25
- Never create an event in the past.
IMPORTANT RULES:
- Saying you did something is NOT doing it. You must call the actual tool.
- To cancel an event: first call search_events, then call delete_event with the id you found.
- To change an event: first call search_events, then call update_event with the id you found.
- Never claim an event was created, updated, or cancelled unless you actually called that tool in this conversation.
- If search_events returns multiple matching events, call delete_event (or update_event) once for EACH matching id.
Given some text (an email or a user message), decide what to do:
- If it describes a NEW event, call create_event.
- If it changes an event that already exists, call search_events to find its id, then update_event.
- If it cancels an event that exists, call search_events to find its id, then delete_event.
- If the text is NOT about a calendar event (ads, newsletters, receipts, bank alerts, spam), call do_nothing.

The user's current events:
{events_summary}

Take the needed actions using the tools. When done, reply with one short sentence describing what you did."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_text},
    ]

    # The agent loop — up to 5 rounds
    for _ in range(105):
        try:
            reply = _call_groq(messages)
        except requests.exceptions.HTTPError:
            # LLM produced a malformed tool call — nudge it and retry
            messages.append({
                "role": "user",
                "content": "Your last tool call was malformed. Please call the tool again with valid JSON arguments.",
            })
            continue
        messages.append(reply)  # remember what the LLM said

        tool_calls = reply.get("tool_calls")
        if not tool_calls:
            # No tools requested — this is the final text answer
            return reply.get("content") or "Done."

        # Run every tool the LLM asked for
        for call in tool_calls:
            name = call["function"]["name"]
            args = json.loads(call["function"]["arguments"])

            try:
                result = dispatch(db, name, args)
            except Exception as e:
                result = f"Error running {name}: {str(e)}"

            if result is None:
                result = "Done."

            messages.append({
                "role": "tool",
                "tool_call_id": call["id"],
                "content": str(result),     # ← force string, never null
            })

    return "Stopped after too many steps."
