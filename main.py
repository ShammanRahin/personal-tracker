from fastapi import FastAPI
from database import engine
from models import Base
from routers import events
from fastapi.middleware.cors import CORSMiddleware
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events.router)


    
@app.get("/")
def hello_page():
    return {"Hello" :"Good Morning"}
