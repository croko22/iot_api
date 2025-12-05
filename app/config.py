from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "YOLO Fire Detection API"
    MODEL_PATH: str = "models/best.pt"  # Default path, can be overridden by env var
    CONFIDENCE_THRESHOLD: float = 0.25

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
