import asyncio
import logging

from app.config import Settings
from app.di import build_container
from worker.celery_app import celery_app

logger = logging.getLogger("astrobot")


@celery_app.task
def summarize_memory(user_id: int):
    """Суммаризация памяти пользователя (User memory summarization).

    Вызывается после завершения сессии или по расписанию.
    """
    settings = Settings()
    container = build_container(settings)
    resolver = container.memory_resolver

    messages = []

    try:
        result = asyncio.run(resolver.summarize_and_save(user_id, messages))
        logger.info("Memory summarized for user %d (version %d)", user_id, result.version)
    except Exception as e:
        logger.error("Memory summarization failed for user %d: %s", user_id, str(e))
