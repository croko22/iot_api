from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from contextlib import asynccontextmanager
from app.schemas import DetectionResult
from app.services import FireDetectionService
from app.dependencies import get_model
from app.config import get_settings, Settings
from ultralytics import YOLO

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load model on startup
    get_model()
    yield
    # Clean up if necessary

from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(
    title="YOLO Fire Detection API",
    description="API for detecting fire in images using YOLO",
    version="1.0.0",
    lifespan=lifespan
)

# Ensure static directory exists
os.makedirs("static/results", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return {"status": "online", "message": "YOLO Fire Detection API is running"}

@app.post("/predict", response_model=DetectionResult)
async def predict(
    file: UploadFile = File(...),
    model: YOLO = Depends(get_model),
    settings: Settings = Depends(get_settings)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        contents = await file.read()
        service = FireDetectionService(model, settings)
        result = service.predict(contents, file.filename)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
