from fastapi import FastAPI, Path ,  HTTPException , Depends
from typing import Optional , List
from pydantic import BaseModel 
from datetime import date , time
from Models import Base , Eventdb
from database import engine , get_db
from sqlalchemy.orm  import Session

Base.metadata.create_all(bind=engine)

app = FastAPI()

class EventCreate(BaseModel):
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
class EventResponse(BaseModel):
    id : int
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
    class Config:
        from_attributes= True
    
    
    
    
    
@app.get("/")
def hello_page():
    return {"Hello" :"Good Morning"}

@app.get("/events/{id}" , response_model=List[EventResponse])
def get_event(id :int = Path(...,description = "insert ID" , gt=0 ,lt=999) , db:Session = Depends(get_db)):
    event = db.query(Eventdb).filter(Eventdb.id ==id).first()
    if not event:
        raise HTTPException(
            status_code=404,
            detail="Not Found"
        )
    return event


@app.get("/events" ,response_model=List[EventResponse])
def get_events(lim: Optional[int] = None , db : Session = Depends(get_db)):
    
    query = db.query(Eventdb)

    if lim :
        query = query.limit(lim)

    return query.all()
        
@app.post("/create_event" , response_model=List[EventResponse])
def create_event( event: EventCreate , db : Session = Depends(get_db)):
    new_event = Eventdb(**event.model_dump())
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    return new_event