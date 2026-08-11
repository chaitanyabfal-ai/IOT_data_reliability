from .celery_app import celery


@celery.task(name="app.tasks.process_sensor_data")
def process_sensor_data(data: dict):
    print(f"Processing data: {data}")
    # TODO: persist to TimescaleDB / perform business logic
    return {"status": "processed", "data": data}