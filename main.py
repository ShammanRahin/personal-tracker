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
    
    
class EventUpdate(BaseModel):
    title : Optional[str]=None
    start_time : Optional[time]=None
    end_time : Optional[time] =None
    start_date : Optional[date]=None
    end_date : Optional[date]= None
    priority : Optional[int]=None
    color : Optional[str]=None
    description : Optional[str]=None
    location : Optional[str]=None
    source : Optional[str]=None
    
    
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
def get_events(skip : int = 0 ,lim: int = 50 , db : Session = Depends(get_db)):
    return db.query(Eventdb).offset(skip).limit(lim).all()
    
        
@app.post("/events" , response_model=List[EventResponse] , status_code=201)
def create_event( event: EventCreate , db : Session = Depends(get_db)):
    new_event = Eventdb(**event.model_dump())
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    return new_event
@app.delete("/events/{id}" , status_code=204)
def delete_event(id : int , db : Session = Depends(get_db)):
    event = db.query(Eventdb).filter(Eventdb.id  == id).first()
    if not event:
        raise HTTPException(
            status_code=404 ,
            detail="Event Not Found"
        )
    db.delete(event)
    db.commit()
    return None
@app.patch("/events/{id}" , response_model=EventResponse )
def update_event(id : int , Payload : EventUpdate , db : Session = Depends(get_db)):
    event = db.query(Eventdb).filter(Eventdb.id == id).first()
    if not event:
        raise HTTPException(
            status_code=204,
            detail="Event Not Found"
        )
    update_event = Payload.model_dump(exclude_unset=True)
    for fields , value in update_event.items():
        setattr(event , fields  , value)
    db.commit()
    db.refresh(event)
    return event