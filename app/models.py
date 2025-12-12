from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime
from app.schemas import SystemStatus

class SensorReading(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    temperature: float
    humidity: float
    smoke_level: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class DetectionEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    annotated_image_url: str
    object_count: int
    has_fire: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SystemLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    status: SystemStatus
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[str] = None

class ThresholdsModel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    temperature_max: float
    gas_max: float
    updated_at: datetime = Field(default_factory=datetime.utcnow)
