from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models import DetectionEvent
import shutil
import uuid
import os

router = APIRouter()

@router.post("/upload/audio")
async def upload_audio(file: UploadFile = File(...)):
    """Upload an audio file for storage."""
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
        
        return {"message": "Audio uploaded", "url": audio_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/media/latest")
def get_latest_media(session: Session = Depends(get_session)):
    """Get links to the latest captured media (photo/audio)."""
    last_detection = session.exec(select(DetectionEvent).order_by(DetectionEvent.timestamp.desc())).first()
    last_photo_url = last_detection.annotated_image_url if last_detection else None
    
    return {
        "latest_photo": last_photo_url,
        "latest_audio": None
    }
