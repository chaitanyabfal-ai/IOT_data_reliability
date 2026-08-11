import logging

from .celery_app import celery

logger = logging.getLogger("iot_queuingfix")


@celery.task(name="app.tasks.process_sensor_data")
def process_sensor_data(data: dict):
    logger.info("Processing data: %s", data)
    # TODO: persist to TimescaleDB / perform business logic
    return {"status": "processed", "data": data}