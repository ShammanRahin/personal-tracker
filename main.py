from fastapi import FastAPI, Path ,  HTTPException
from typing import Optional
from pydantic import BaseModel 
from datetime import date , time
app = FastAPI()

class Event(BaseModel):
    ID : int
    title : str
    start_time : time
    end_time : Optional[time] =None
    start_date : date
    end_date : Optional[date]= None
    priority : int
    color : str
    description : str
    location : str
    source : str
    
    
    
    
events = {
    1: Event(
        ID=1,
        title="Quiz",
        start_time=time(10, 30),
        end_time=time(11, 30),
        start_date=date(2026, 5, 9),
        end_date=date(2026, 5, 9),
        priority=1,
        color="red",
        description="Math quiz event",
        location="School",
        source="Gmail"
    ),
    2: Event(
        ID=2,
        title="Quiz 2",
        start_time=time(10, 30),
        end_time=time(11, 30),
        start_date=date(2026, 5, 9),
        end_date=date(2026, 5, 9),
        priority=1,
        color="red",
        description="Math quiz event",
        location="School",
        source="Gmail"
    )
}
@app.get("/events/{ID}")
def get_event(ID:int = Path(...,description = "insert ID" , gt=0 ,lt=999)):
    if ID not in events:
        raise HTTPException(
            status_code=404,
            detail="Not Found"
        )
    return events.get(ID,{"data" : "Not Found"})
@app.get("/events")
def get_events(lim: Optional[int] = None):
    
    event_list = list(events.values())

    if lim:
        return event_list[:lim]

    return event_list
        
@app.post("/create_event/{event_id}")
def create_event(event_id : int , event: Event):
    if event_id in events:
        raise HTTPException(
            status_code=404,
            detail="Student Exists"
        )
    events[event_id] = event
    return events[event_id]