from celery.schedules import crontab

from worker.celery_app import celery_app

# Расписание периодических задач (Celery beat schedule — Phase 4)
celery_app.conf.beat_schedule = {
    "check-session-timeouts": {
        "task": "worker.tasks.session_tasks.check_session_timeout",
        "schedule": crontab(minute="*/5"),
    },
}
