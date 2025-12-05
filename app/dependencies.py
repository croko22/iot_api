from ultralytics import YOLO
from app.config import get_settings
from functools import lru_cache
import os

# Global variable to hold the model instance
_model_instance = None

def get_model():
    global _model_instance
    if _model_instance is None:
        settings = get_settings()
        # Check if custom model exists, otherwise use standard yolov8n as fallback/placeholder
        # In production, you'd likely want to fail if the specific model isn't found.
        model_path = settings.MODEL_PATH
        
        if not os.path.exists(model_path):
            print(f"Warning: Model not found at {model_path}. Using 'models/best.pt' for demonstration.")
            model_path = "models/best.pt" # Auto-downloads
            
        print(f"Loading model from {model_path}...")
        _model_instance = YOLO(model_path)
        
    return _model_instance
