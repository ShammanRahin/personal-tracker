from sqlalchemy.orm import Session
from models import Routinedb
from schemas import RoutineCreate


def create_routine(db: Session, routine: RoutineCreate) -> Routinedb:
    new_routine = Routinedb(**routine.model_dump())
    db.add(new_routine)
    db.commit()
    db.refresh(new_routine)
    return new_routine


def get_routines(db: Session, active_only: bool = True) -> list:
    query = db.query(Routinedb)
    if active_only:
        query = query.filter(Routinedb.active == True)
    return query.all()


def get_routine(db: Session, id: int) -> Routinedb | None:
    return db.query(Routinedb).filter(Routinedb.id == id).first()


def deactivate_routine(db: Session, id: int) -> bool:
    routine = db.query(Routinedb).filter(Routinedb.id == id).first()
    if not routine:
        return False
    routine.active = False
    db.commit()
    return True