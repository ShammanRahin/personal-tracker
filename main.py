from fastapi import FastAPI
from database import engine
from models import Base
from routers import events
from fastapi.middleware.cors import CORSMiddleware
Base.metadata.create_all(bind=engine)
from routers import routines as routines_router
import os
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://*.vercel.app",           
        os.getenv("FRONTEND_URL", ""),    
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events.router)
app.include_router(routines_router.router)

    
@app.get("/")
def hello_page():
    return {"Hello" :"Good Morning"}
