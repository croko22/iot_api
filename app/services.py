from PIL import Image
from ultralytics import YOLO
from app.schemas import DetectionResult, Box
from app.config import Settings
from app.models import DetectionEvent
from sqlmodel import Session
import io

class FireDetectionService:
    def __init__(self, model: YOLO, settings: Settings, db: Session):
        self.model = model
        self.settings = settings
        self.db = db

    def predict(self, image_bytes: bytes, filename: str) -> DetectionResult:
        image = Image.open(io.BytesIO(image_bytes))
        
        # Run inference
        results = self.model.predict(image, conf=self.settings.CONFIDENCE_THRESHOLD)
        
        detections = []
        for result in results:
            for box in result.boxes:
                # Get box coordinates
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                class_name = result.names[class_id]
                
                detections.append(Box(
                    x1=x1,
                    y1=y1,
                    x2=x2,
                    y2=y2,
                    confidence=confidence,
                    class_id=class_id,
                    class_name=class_name
                ))
        
        message = f"Found {len(detections)} objects."
        if len(detections) == 0:
            message = "No fire detected."
        
        # Save annotated image
        import os
        import uuid
        
        # Create a unique filename
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{uuid.uuid4().hex}{ext}"
        save_path = os.path.join("static/results", unique_filename)
        
        # Plot results on the image
        # plot() returns a numpy array (BGR), we need to convert it back to RGB and save
        im_array = results[0].plot()  # plot() returns BGR numpy array
        im = Image.fromarray(im_array[..., ::-1])  # RGB PIL Image
        im.save(save_path)
        
        annotated_image_url = f"/static/results/{unique_filename}"
        
        # Save to DB
        has_fire = any(d.class_name == 'fire' for d in detections)
        event = DetectionEvent(
            filename=filename,
            annotated_image_url=annotated_image_url,
            object_count=len(detections),
            has_fire=has_fire
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        return DetectionResult(
            filename=filename,
            detections=detections,
            message=message,
            annotated_image_url=annotated_image_url
        )
