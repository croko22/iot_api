from pydantic import BaseModel
from typing import List

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
