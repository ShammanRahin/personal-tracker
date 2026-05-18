from typing import Optional
from pydantic import BaseModel 
from datetime import date , time


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
    source : Optional[str] =None
    source_id :Optional[str] =None
    
    
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
    source_id :Optional[str] =None
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