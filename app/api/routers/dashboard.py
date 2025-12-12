from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.database import get_session
from app.models import DetectionEvent, SensorReading, ThresholdsModel
from app.schemas import DashboardResponse, Thresholds, SystemStatus, SensorData, ThresholdsUpdate

router = APIRouter()

def get_latest_sensor_data(session: Session) -> SensorData:
    """Helper to fetch latest sensor data."""
    sensor_reading = session.exec(select(SensorReading).order_by(SensorReading.timestamp.desc())).first()
    if not sensor_reading:
        return SensorData(temperature=0, humidity=0, smoke_level=0)
    return SensorData(
        temperature=sensor_reading.temperature,
        humidity=sensor_reading.humidity,
        smoke_level=sensor_reading.smoke_level,
        timestamp=str(sensor_reading.timestamp)
    )

def get_current_thresholds(session: Session) -> Thresholds:
    """Helper to fetch current thresholds."""
    current = session.exec(select(ThresholdsModel).order_by(ThresholdsModel.updated_at.desc())).first()
    if not current:
        return Thresholds() # Default
    return Thresholds(temperature_max=current.temperature_max, gas_max=current.gas_max)

def get_current_status(session: Session) -> SystemStatus:
    """Determine overall system status based on sensors and detections."""
    sensor_data = get_latest_sensor_data(session)
    last_detection = session.exec(select(DetectionEvent).order_by(DetectionEvent.timestamp.desc())).first()
    thresholds = get_current_thresholds(session)
    
    status = SystemStatus.NORMAL
    if sensor_data.temperature > thresholds.temperature_max or sensor_data.smoke_level > thresholds.gas_max:
        status = SystemStatus.RIESGO
    
    if last_detection and last_detection.has_fire:
         status = SystemStatus.CONFIRMADO
    
    return status

@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(session: Session = Depends(get_session)):
    """Aggregate data for the main dashboard view."""
    sensor_data = get_latest_sensor_data(session)
    status = get_current_status(session)
    thresholds = get_current_thresholds(session)
    
    last_detection = session.exec(select(DetectionEvent).order_by(DetectionEvent.timestamp.desc())).first()
    last_photo_url = last_detection.annotated_image_url if last_detection else None

    return DashboardResponse(
        status=status,
        sensors=sensor_data,
        thresholds=thresholds,
        last_photo_url=last_photo_url,
        last_audio_url=None 
    )

@router.get("/status")
def get_status(session: Session = Depends(get_session)):
    """Get concise system status."""
    return {"status": get_current_status(session)}

@router.get("/thresholds", response_model=Thresholds)
async def fetch_thresholds(session: Session = Depends(get_session)):
    """Fetch current system thresholds."""
    return get_current_thresholds(session)

@router.post("/thresholds", response_model=Thresholds)
async def update_threshold(data: ThresholdsUpdate, session: Session = Depends(get_session)):
    """Update system thresholds."""
    current = session.exec(select(ThresholdsModel).order_by(ThresholdsModel.updated_at.desc())).first()
    
    new_temp = data.temperature_max if data.temperature_max is not None else (current.temperature_max if current else 50.0)
    new_gas = data.gas_max if data.gas_max is not None else (current.gas_max if current else 300.0)
    
    new_thresholds = ThresholdsModel(temperature_max=new_temp, gas_max=new_gas)
    session.add(new_thresholds)
    session.commit()
    session.refresh(new_thresholds)
    
    return Thresholds(temperature_max=new_thresholds.temperature_max, gas_max=new_thresholds.gas_max)
