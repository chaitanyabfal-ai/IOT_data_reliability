import logging

from .celery_app import celery

logger = logging.getLogger("iot_queuingfix")


@celery.task(name="app.tasks.process_sensor_data")
def process_sensor_data(data):
    """Process a single reading or a batch of readings.

    Accepts either a dict for a single reading or a list of dicts for a batch.
    """
    if isinstance(data, list):
        logger.info("Processing batch of %d readings", len(data))
        # TODO: persist batch to TimescaleDB / perform business logic for each item
        for item in data:
            logger.debug("Processing item in batch: %s", item)
        return {"status": "processed", "count": len(data)}

    logger.info("Processing data: %s", data)
    # TODO: persist to TimescaleDB / perform business logic
    return {"status": "processed", "data": data}