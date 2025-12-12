from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.routers import sensors, dashboard, media, predict, websockets
from app.dependencies import get_model
from app.database import create_db_and_tables
import os
from fastapi.staticfiles import StaticFiles

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for the FastAPI app.
    - Loads the YOLO model.
    - Creates database tables.
    - Ensures necessary static directories exist.
    """
    get_model()
    create_db_and_tables()
    os.makedirs("static/audio", exist_ok=True)
    os.makedirs("static/results", exist_ok=True)
    yield

app = FastAPI(
    title="YOLO Fire Detection API",
    description="API for detecting fire in images using YOLO with real-time WebSocket alerts.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include Routers
app.include_router(sensors.router, tags=["Sensors"])
app.include_router(dashboard.router, tags=["Dashboard"])
app.include_router(media.router, tags=["Media"])
app.include_router(predict.router, tags=["Prediction"])
app.include_router(websockets.router, tags=["WebSockets"])

@app.get("/")
def read_root():
    return {"status": "online", "message": "YOLO Fire Detection API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
