import asyncio
import logging

from app.config import Settings
from app.di import build_container
from worker.celery_app import celery_app

logger = logging.getLogger("astrobot")


@celery_app.task
def check_session_timeout():
    """Проверка таймаутов сессий и завершение просроченных (Check and end stale sessions)."""
    settings = Settings()
    container = build_container(settings)
    session_service = container.session_service

    try:
        stale = asyncio.run(session_service.check_timeouts())
        if stale:
            logger.info("Ended %d stale sessions", len(stale))
        else:
            logger.debug("No stale sessions found")
    except Exception as e:
        logger.error("Session timeout check failed: %s", str(e))
