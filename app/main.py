import logging
from typing import Any, List

from fastapi import FastAPI

from . import config
from .on_prem_fetcher import fetch_on_prem_data
from .schemas import SensorData, SensorDataResponse
from .tasks import process_sensor_data

logger = logging.getLogger("iot_queuingfix")

app = FastAPI(title="IoT Queuing Fix", version="1.0.0")


@app.on_event("startup")
async def startup_event() -> None:
    logger.info("IoT Queuing Fix application started.")


@app.get("/health")
async def health_check() -> dict[str, str]:
    logger.info("Health check requested.")
    return {"status": "ok"}


@app.get("/on-prem-data")
async def get_on_prem_data() -> dict[str, Any]:
    logger.info("Fetching on-prem data endpoint requested.")
    return fetch_on_prem_data()


@app.post("/sensor-data/", response_model=SensorDataResponse)
async def receive_sensor_data(data: SensorData) -> SensorDataResponse:
    payload = data.model_dump() if hasattr(data, "model_dump") else data.dict()
    logger.info("Received sensor payload: %s", payload)
    process_sensor_data.delay(payload)
    return {"status": "queued", "data": payload}


def _chunked(iterable: List[dict], size: int):
    for i in range(0, len(iterable), size):
        yield iterable[i : i + size]


@app.post("/sensor-data/batch")
async def receive_sensor_data_batch(data: List[SensorData]) -> dict[str, int]:
    """Accept a list of sensor readings and enqueue them in batches.

    This reduces Celery task count by grouping many readings into fewer tasks.
    The batch size is controlled by the `BATCH_SIZE` environment variable.
    """
    # normalize to list[dict]
    payloads: List[dict] = [
        (d.model_dump() if hasattr(d, "model_dump") else d.dict()) for d in data
    ]
    batch_size = getattr(config, "BATCH_SIZE", 500)
    batches = list(_chunked(payloads, batch_size))
    for batch in batches:
        process_sensor_data.delay(batch)

    return {"status": "queued", "batches": len(batches), "items": len(payloads)}