from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base

# Base class for SQLAlchemy models
Base = declarative_base()

# Model for the sensor_data table in TimescaleDB
class SensorData(Base):
    __tablename__ = 'sensor_data'

    # Columns
    id = Column(Integer, primary_key=True, autoincrement=True)  # Auto-incremented primary key
    device_id = Column(String(50), nullable=False)             # Unique identifier for the IoT device
    temperature = Column(Float, nullable=False)                # Temperature reading
    humidity = Column(Float, nullable=False)                   # Humidity reading
    time = Column(DateTime, nullable=False)                    # Timestamp of the reading