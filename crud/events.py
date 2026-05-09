from fastapi import HTTPException
from sqlalchemy.orm import Session
from models import Eventdb
from schemas import EventCreate , EventUpdate
from database import get_db
def get_event(db : Session , id : int):
    event = db.query(Eventdb).filter(Eventdb.id ==id).first()
    return event

def get_events(db : Session ,skip : int = 0 ,lim: int = 50 ):
    return db.query(Eventdb).offset(skip).limit(lim).all()

def create_event( db : Session ,event: EventCreate ):
    new_event = Eventdb(**event.model_dump())
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    return new_event

def delete_event(db : Session ,id : int ):
    event = db.query(Eventdb).filter(Eventdb.id  == id).first()
    if not event:
        return False
    db.delete(event)
    db.commit()
    return True

def update_event(db : Session ,id : int , payload : EventUpdate):
    event = db.query(Eventdb).filter(Eventdb.id == id).first()
    update_event = payload.model_dump(exclude_unset=True)
    for fields , value in update_event.items():
        setattr(event , fields  , value)
    db.commit()
    db.refresh(event)
    return event