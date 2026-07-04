from worker.celery_app import celery_app


@celery_app.task
def check_session_timeout():
    """Проверка таймаутов сессий (Placeholder — будет реализовано в Phase 4)."""
    pass
