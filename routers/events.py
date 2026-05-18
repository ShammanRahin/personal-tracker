from fastapi import FastAPI, Path ,Depends , APIRouter , HTTPException
from schemas import EventCreate , EventResponse , EventUpdate
from typing import List 
from sqlalchemy.orm import Session 
from database import get_db
from crud import events as crud_events
from pydantic import BaseModel
from services.extractor import extract_event as extract_create
from services.sync import sync_gmail as sync_create
from services.agent import run_agent
class ExtractEvent(BaseModel):
    text:str
    
    
router = APIRouter(prefix="/events" , tags=["events"])
class ChatMessage(BaseModel):
    message: str

@router.post("/chat")
def chat(payload: ChatMessage, db: Session = Depends(get_db)):
    events = crud_events.get_events(db)
    try:
        reply = run_agent(db, payload.message, events)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")
    return {"reply": reply}


@router.get("/search")
def search_events(query : str , query_title : str , db : Session = Depends(get_db)):
    return crud_events.search_events(query=query , query_title=query_title , db=db)

@router.get("/{id}" , response_model=EventResponse)
def get_event(id :int = Path(...,description = "insert ID" , gt=0 ,lt=999) , db:Session = Depends(get_db)):
    event = crud_events.get_event(db , id)
    if not event:
        raise HTTPException(
            status_code=404 , 
            detail="Event Does not Exist"
        )
    return event


@router.get("" ,response_model=List[EventResponse])
def get_events(skip : int = 0 ,lim: int = 50 , db : Session = Depends(get_db)):
    return crud_events.get_events(db , skip=skip , lim=lim)
    
        
@router.post("" , response_model=EventResponse, status_code=201)
def create_event( event: EventCreate , db : Session = Depends(get_db)):
    success = crud_events.create_event(db , event)
    if not success:
        raise HTTPException(
            status_code=404 , 
            detail= "Event already Exists"
        )
    
    return success

@router.delete("/{id}" , status_code=204)
def delete_event(id : int , db : Session = Depends(get_db)):
    if not crud_events.delete_event(db, id):
        raise HTTPException(status_code=404, detail="Event not found")
    

@router.patch("/{id}" , response_model=EventResponse ,status_code=200)
def update_event(id : int , payload : EventUpdate , db : Session = Depends(get_db)):
    event = crud_events.update_event(db, id, payload)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.post("/extract" , response_model=EventResponse , status_code=201)
def extract_event(payload : ExtractEvent ,  db : Session = Depends(get_db)):
    try:
        event = extract_create(payload.text)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Could not extract event: {str(e)}"
        )
    return crud_events.create_event(db, event)
@router.post("/sync" , status_code=201)
def sync_gmail( limit : int = 10, db : Session = Depends(get_db) ):
    try:
        events = sync_create(limit= limit , db=db)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Could not sync gmail: {str(e)}"
        )
    return events
