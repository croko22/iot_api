from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "YOLO Fire Detection API"
    MODEL_PATH: str = "models/best.pt"  # Default path, can be overridden by env var
    CONFIDENCE_THRESHOLD: float = 0.25
    
    # Mailtrap Settings
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str = "fire-alert@iot-system.com"
    MAIL_TO: str = "admin@example.com"
    MAIL_SERVER: str = "sandbox.smtp.mailtrap.io"
    MAIL_PORT: int = 2525

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
