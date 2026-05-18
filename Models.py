from database import Base
from sqlalchemy import  Column , Integer , String , Date , Time ,Boolean


# ID : int
#     title : str
#     start_time : time
#     end_time : Optional[time] =None
#     start_date : date
#     end_date : Optional[date]= None
#     priority : int
#     color : str
#     description : str
#     location : str
#     source : str

class Routinedb(Base):
    __tablename__ = "Routines"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    day_of_week = Column(Integer, nullable=False)  
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=True)
    location = Column(String, default="")
    color = Column(String, default="academic")
    active = Column(Boolean, default=True)
class Eventdb(Base):
    __tablename__ = "Events"
    
    id = Column(Integer , primary_key=True , index=True)
    title = Column(String ,nullable=False)
    start_time = Column(Time , nullable=False)
    end_time = Column(Time)
    start_date = Column(Date , nullable=False)
    end_date = Column(Date)
    priority = Column(Integer)
    color = Column(String)
    description = Column(String)
    location = Column(String)
    source = Column(String , nullable=True)
    source_id = Column( String,nullable=True )
    routine_id = Column(Integer, nullable=True)
    is_routine = Column(Boolean, default=False)