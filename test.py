from database import SessionLocal
from crud import events as crud_events
from services.agent import run_agent

db = SessionLocal()
events = crud_events.get_events(db)

# Test 1 — create
print(run_agent(db, "I have a dentist appointment next Monday at 3pm", events))

# Test 2 — ignore (the Step 9 garbage problem)
print(run_agent(db, "FLAT 50% OFF — shop the summer sale now!", events))

# Test 3 — delete (needs search first)
events = crud_events.get_events(db)  # refresh after the create
print(run_agent(db, "cancel my dentist appointment", events))

db.close()