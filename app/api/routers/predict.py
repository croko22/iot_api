from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlmodel import Session, select
from ultralytics import YOLO
from datetime import datetime
from app.database import get_session
from app.dependencies import get_model
from app.config import get_settings, Settings
from app.services import FireDetectionService
from app.schemas import DetectionResult
from app.models import DetectionEvent
from app.api.routers.websockets import manager
from app.state import state

router = APIRouter()

@router.post("/predict", response_model=DetectionResult)
async def predict(
    file: UploadFile = File(...),
    model: YOLO = Depends(get_model),
    settings: Settings = Depends(get_settings),
    session: Session = Depends(get_session)
):
    """
    Perform fire detection on an uploaded image.
    
    If fire is detected with sufficient confidence, a confirmed fire alert is broadcast.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        contents = await file.read()
        service = FireDetectionService(model, settings, session)
        result = service.predict(contents, file.filename)
        
        # Check if fire was detected in the image
        has_fire = any(d.class_name == 'fire' for d in result.detections)
        
        if has_fire:
            state.is_fire_detected = True
            # Notify dashboards of confirmed fire
            dashboard_message = {
                "type": "fire_confirmed",
                "image_url": result.annotated_image_url,
                "confidence": max([d.confidence for d in result.detections if d.class_name=='fire'], default=0),
                "message": "Fire confirmed by visual analysis",
                "timestamp": datetime.now().isoformat()
            }
            await manager.notify_dashboards(dashboard_message)
            
            # Send Email Alert
            from app.notifications import send_email_alert
            send_email_alert(
                subject=f"🔥 FIRE CONFIRMED (Visual): {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                body=f"Visual analysis confirmed fire!\n\nImage: {result.annotated_image_url}\nConfidence: {dashboard_message['confidence']:.2f}\n\nPlease check the system immediately."
            )
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/detections")
def get_detection_history(session: Session = Depends(get_session), limit: int = 10):
    """Retrieve history of detection events."""
    events = session.exec(select(DetectionEvent).order_by(DetectionEvent.timestamp.desc()).limit(limit)).all()
    return events
