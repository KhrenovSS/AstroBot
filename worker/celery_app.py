from celery import Celery

from app.config import Settings

settings = Settings()

celery_app = Celery(
    "astrobot",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["worker.tasks.memory_tasks", "worker.tasks.session_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
