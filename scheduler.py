import logging
from apscheduler.schedulers.background import BackgroundScheduler
from database import SessionLocal
from services.sync import sync_gmail
from services.sync_classroom import sync_classroom

logger = logging.getLogger(__name__)


def _job_sync_gmail():
    db = SessionLocal()
    try:
        result = sync_gmail(db)
        logger.info("Scheduled gmail sync: %s", result)
    except Exception:
        logger.exception("Scheduled gmail sync failed")
    finally:
        db.close()


def _job_sync_classroom():
    db = SessionLocal()
    try:
        result = sync_classroom(db)
        logger.info("Scheduled classroom sync: %s", result)
    except Exception:
        logger.exception("Scheduled classroom sync failed")
    finally:
        db.close()


def create_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        _job_sync_gmail,
        trigger="interval",
        minutes=30,
        id="gmail_sync",
        replace_existing=True,
        misfire_grace_time=60,
    )
    scheduler.add_job(
        _job_sync_classroom,
        trigger="interval",
        minutes=60,
        id="classroom_sync",
        replace_existing=True,
        misfire_grace_time=120,
    )
    return scheduler
