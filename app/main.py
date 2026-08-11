from typing import Any

from fastapi import FastAPI

from .on_prem_fetcher import fetch_on_prem_data
from .schemas import SensorData, SensorDataResponse
from .tasks import process_sensor_data

app = FastAPI(title="IoT Queuing Fix", version="1.0.0")


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/on-prem-data")
async def get_on_prem_data() -> dict[str, Any]:
    return fetch_on_prem_data()


@app.post("/sensor-data/", response_model=SensorDataResponse)
async def receive_sensor_data(data: SensorData) -> SensorDataResponse:
    payload = data.model_dump() if hasattr(data, "model_dump") else data.dict()
    process_sensor_data.delay(payload)
    return {"status": "queued", "data": payload}