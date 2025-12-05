from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.schemas import DetectionResult, DashboardResponse, SensorData, Thresholds, SystemStatus
from app.services import FireDetectionService
from app.dependencies import get_model
from app.config import get_settings, Settings
from app.database import create_db_and_tables, get_session
from app.models import SensorReading, DetectionEvent, SystemLog
from sqlmodel import Session, select
from ultralytics import YOLO
import shutil
import uuid
import os
from fastapi.staticfiles import StaticFiles

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load model on startup
    get_model()
    # Create DB tables
    create_db_and_tables()
    # Ensure audio directory exists
    os.makedirs("static/audio", exist_ok=True)
    yield
    # Clean up if necessary

app = FastAPI(
    title="YOLO Fire Detection API",
    description="API for detecting fire in images using YOLO",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Ensure static directory exists
os.makedirs("static/results", exist_ok=True)
# os.makedirs("static/audio", exist_ok=True) # This is now handled in lifespan

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return {"status": "online", "message": "YOLO Fire Detection API is running"}

def get_latest_sensor_data(session: Session) -> SensorData:
    sensor_reading = session.exec(select(SensorReading).order_by(SensorReading.timestamp.desc())).first()
    if not sensor_reading:
        return SensorData(temperature=0, humidity=0, smoke_level=0)
    return SensorData(
        temperature=sensor_reading.temperature,
        humidity=sensor_reading.humidity,
        smoke_level=sensor_reading.smoke_level,
        timestamp=str(sensor_reading.timestamp)
    )

def get_current_status(session: Session) -> SystemStatus:
    sensor_data = get_latest_sensor_data(session)
    last_detection = session.exec(select(DetectionEvent).order_by(DetectionEvent.timestamp.desc())).first()
    
    thresholds = Thresholds() # In-memory defaults for now
    
    status = SystemStatus.NORMAL
    if sensor_data.temperature > thresholds.temp_alert or sensor_data.smoke_level > thresholds.smoke_alert:
        status = SystemStatus.RIESGO
    
    if last_detection and last_detection.has_fire:
         status = SystemStatus.CONFIRMADO
    
    return status

@app.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(session: Session = Depends(get_session)):
    sensor_data = get_latest_sensor_data(session)
    status = get_current_status(session)
    
    last_detection = session.exec(select(DetectionEvent).order_by(DetectionEvent.timestamp.desc())).first()
    last_photo_url = last_detection.annotated_image_url if last_detection else None

    return DashboardResponse(
        status=status,
        sensors=sensor_data,
        thresholds=Thresholds(),
        last_photo_url=last_photo_url,
        last_audio_url=None 
    )

@app.get("/status")
def get_status(session: Session = Depends(get_session)):
    return {"status": get_current_status(session)}

@app.get("/sensors", response_model=SensorData)
def get_sensors(session: Session = Depends(get_session)):
    return get_latest_sensor_data(session)

@app.get("/media/latest")
def get_latest_media(session: Session = Depends(get_session)):
    last_detection = session.exec(select(DetectionEvent).order_by(DetectionEvent.timestamp.desc())).first()
    last_photo_url = last_detection.annotated_image_url if last_detection else None
    # Assuming we might store audio in DB later, for now return null or implement a table
    return {
        "latest_photo": last_photo_url,
        "latest_audio": None
    }

@app.post("/sensors")
def update_sensors(data: SensorData, session: Session = Depends(get_session)):
    reading = SensorReading(
        temperature=data.temperature,
        humidity=data.humidity,
        smoke_level=data.smoke_level
    )
    session.add(reading)
    session.commit()
    return {"message": "Sensors updated"}

@app.post("/config/thresholds")
def update_thresholds(data: Thresholds):
    # For now, just return them as we haven't persisted them
    return {"message": "Thresholds updated (in-memory only for now)", "thresholds": data}

@app.post("/upload/audio")
async def upload_audio(file: UploadFile = File(...)):
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="File must be an audio file")
    
    try:
        # Save audio file
        name, ext = os.path.splitext(file.filename)
        unique_filename = f"{name}_{uuid.uuid4().hex}{ext}"
        save_path = os.path.join("static/audio", unique_filename)
        
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        audio_url = f"/static/audio/{unique_filename}"
        # We should save this to DB too if we want persistence, but for now just return URL
        
        return {"message": "Audio uploaded", "url": audio_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict", response_model=DetectionResult)
async def predict(
    file: UploadFile = File(...),
    model: YOLO = Depends(get_model),
    settings: Settings = Depends(get_settings),
    session: Session = Depends(get_session)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        contents = await file.read()
        service = FireDetectionService(model, settings, session)
        result = service.predict(contents, file.filename)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history/sensors")
def get_sensor_history(session: Session = Depends(get_session), limit: int = 10):
    readings = session.exec(select(SensorReading).order_by(SensorReading.timestamp.desc()).limit(limit)).all()
    return readings

@app.get("/history/detections")
def get_detection_history(session: Session = Depends(get_session), limit: int = 10):
    events = session.exec(select(DetectionEvent).order_by(DetectionEvent.timestamp.desc()).limit(limit)).all()
    return events

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
