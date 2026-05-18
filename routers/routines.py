from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas import RoutineResponse
from crud import routines as crud_routines
from services.routine_extractor import (
    extract_routine_from_image,
    extract_routine_from_text,
)
from services.recurrence import generate_upcoming_events

router = APIRouter(prefix="/routines", tags=["routines"])


@router.post("/upload-image")
async def upload_routine_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    image_bytes = await file.read()
    mime_type = file.content_type or "image/jpeg"

    try:
        extracted = extract_routine_from_image(image_bytes, mime_type)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Could not extract routine from image: {str(e)}"
        )

    created_routines = []
    total_events = 0
    for r in extracted:
        routine = crud_routines.create_routine(db, r)
        count = generate_upcoming_events(db, routine, weeks_ahead=12)
        total_events += count
        created_routines.append({
            "id": routine.id,
            "title": routine.title,
            "day_of_week": routine.day_of_week,
            "start_time": str(routine.start_time),
        })

    return {
        "routines_created": len(created_routines),
        "events_generated": total_events,
        "routines": created_routines,
    }


@router.post("/upload-text")
async def upload_routine_text(
    text: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        extracted = extract_routine_from_text(text)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Could not extract routine from text: {str(e)}"
        )

    created_routines = []
    total_events = 0
    for r in extracted:
        routine = crud_routines.create_routine(db, r)
        count = generate_upcoming_events(db, routine, weeks_ahead=12)
        total_events += count
        created_routines.append({
            "id": routine.id,
            "title": routine.title,
            "day_of_week": routine.day_of_week,
            "start_time": str(routine.start_time),
        })

    return {
        "routines_created": len(created_routines),
        "events_generated": total_events,
        "routines": created_routines,
    }


@router.get("", response_model=List[RoutineResponse])
def get_routines(db: Session = Depends(get_db)):
    return crud_routines.get_routines(db, active_only=True)


@router.delete("/{id}", status_code=204)
def cancel_routine(id: int, db: Session = Depends(get_db)):
    if not crud_routines.deactivate_routine(db, id):
        raise HTTPException(status_code=404, detail="Routine not found")