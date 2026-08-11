from celery import Celery
from . import config


celery = Celery(
    "app",
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_RESULT_BACKEND,
)

celery.conf.update(
    task_serializer=getattr(config, "CELERY_TASK_SERIALIZER", "json"),
    result_serializer=getattr(config, "CELERY_RESULT_SERIALIZER", "json"),
    timezone=getattr(config, "CELERY_TIMEZONE", "UTC"),
    accept_content=["json"],
)
