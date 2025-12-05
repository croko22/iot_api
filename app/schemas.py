from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class SystemStatus(str, Enum):
    NORMAL = "Normal"
    RIESGO = "Riesgo"
    CONFIRMADO = "Confirmado"

class SensorData(BaseModel):
    temperature: float
    humidity: float
    smoke_level: float
    timestamp: Optional[str] = None

class Thresholds(BaseModel):
    temp_alert: float = 50.0
    smoke_alert: float = 300.0

class Box(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    class_id: int
    class_name: str

class DetectionResult(BaseModel):
    filename: str
    detections: List[Box]
    message: str
    annotated_image_url: str = None

class DashboardResponse(BaseModel):
    status: SystemStatus
    sensors: SensorData
    thresholds: Thresholds
    last_photo_url: Optional[str] = None
    last_audio_url: Optional[str] = None
