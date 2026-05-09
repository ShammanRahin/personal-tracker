from fastapi import FastAPI
from database import engine
from models import Base
from routers import events

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(events.router)


    
@app.get("/")
def hello_page():
    return {"Hello" :"Good Morning"}
