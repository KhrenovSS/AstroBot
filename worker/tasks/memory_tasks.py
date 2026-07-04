from worker.celery_app import celery_app


@celery_app.task
def summarize_memory(user_id: int):
    """Суммаризация памяти пользователя (Placeholder — будет реализовано в Phase 4)."""
    pass
