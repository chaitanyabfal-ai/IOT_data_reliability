from pydantic import BaseModel
from datetime import datetime

# Schema for incoming sensor data (request validation)
class SensorData(BaseModel):
    device_id: str
    temperature: float
    humidity: float
    time: datetime  # Timestamp of the sensor reading

# Schema for response after processing
class SensorDataResponse(BaseModel):
    status: str
    data: dict  # Contains the original sensor data