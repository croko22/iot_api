from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from datetime import datetime
from app.database import get_session
from app.models import SensorReading
from app.schemas import SensorData
from app.services import FireDetectionService
from app.api.routers.websockets import manager
from app.state import state

router = APIRouter()

@router.post("/sensors")
async def update_sensors(data: SensorData, session: Session = Depends(get_session)):
    """
    Receive new sensor data, persist it, and check for fire risks.
    
    If risk is detected, triggers alerts to monitoring dashboards and cameras.
    """
    # Check if fire mode is already active
    if state.is_fire_detected:
        return {"message": "Fire already detected. Sensor updates paused to prevent overload."}

    # Persist reading
    reading = SensorReading(
        temperature=data.temperature,
        humidity=data.humidity,
        smoke_level=data.smoke_level,
        timestamp=datetime.now()
    )
    session.add(reading)
    session.commit()
    session.refresh(reading)

    # Risk evaluation
    fire_alert = FireDetectionService.check_sensor_risk(data, session)
    
    # Broadcast to dashboards
    dashboard_message = {
        "type": "sensor_reading",
        "data": data.dict(),
        "fire_risk": fire_alert,
        "timestamp": datetime.now().isoformat()
    }
    await manager.notify_dashboards(dashboard_message)
    
    # Broadcast to cameras if risk is high
    email_sent = False
    email_error = None
    camera_alert = False
    
    if fire_alert:
        state.is_fire_detected = True
        # Send Email Alert
        from app.notifications import send_email_alert
        email_sent, email_error = send_email_alert(
            subject=f"🔥 FIRE RISK DETECTED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            body=f"High risk detected!\n\nTemperature: {data.temperature}°C\nSmoke Level: {data.smoke_level}\n\nPlease check the system immediately."
        )

        camera_message = {
            "type": "search_image_alert",
            "data": data.dict(),
            "message": "Possible fire detected, capture image",
            "timestamp": datetime.now().isoformat()
        }
        await manager.notify_cameras(camera_message)
        camera_alert = True

    return {
        "message": "Sensors updated",
        "fire_alert": fire_alert,
        "email_sent": email_sent,
        "email_error": email_error,
        "camera_alert": camera_alert
    }

@router.get("/sensors", response_model=SensorData)
def get_sensors(session: Session = Depends(get_session)):
    """Retrieve the latest sensor reading."""
    sensor_reading = session.exec(select(SensorReading).order_by(SensorReading.timestamp.desc())).first()
    if not sensor_reading:
        return SensorData(temperature=0, humidity=0, smoke_level=0)
    return SensorData(
        temperature=sensor_reading.temperature,
        humidity=sensor_reading.humidity,
        smoke_level=sensor_reading.smoke_level,
        timestamp=str(sensor_reading.timestamp)
    )

@router.get("/history/sensors")
def get_sensor_history(session: Session = Depends(get_session), limit: int = 10):
    """Retrieve historical sensor readings."""
    readings = session.exec(select(SensorReading).order_by(SensorReading.timestamp.desc()).limit(limit)).all()
    return readings
