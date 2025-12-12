from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Literal, List
from datetime import datetime

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.dashboard_connections: List[WebSocket] = []
        self.camera_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket, client_type: str):
        await websocket.accept()
        if client_type == "dashboard":
            self.dashboard_connections.append(websocket)
        elif client_type == "camera":
            self.camera_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket, client_type: str):
        if client_type == "dashboard" and websocket in self.dashboard_connections:
            self.dashboard_connections.remove(websocket)
        elif client_type == "camera" and websocket in self.camera_connections:
            self.camera_connections.remove(websocket)
    
    async def notify_cameras(self, message: dict):
        """Notify only camera clients"""
        dead_connections = []
        for connection in self.camera_connections:
            try:
                await connection.send_json(message)
            except:
                dead_connections.append(connection)
        
        for conn in dead_connections:
            self.camera_connections.remove(conn)
    
    async def notify_dashboards(self, message: dict):
        """Notify only dashboard clients"""
        dead_connections = []
        for connection in self.dashboard_connections:
            try:
                await connection.send_json(message)
            except:
                dead_connections.append(connection)
        
        for conn in dead_connections:
            self.dashboard_connections.remove(conn)

# Singleton instance
manager = ConnectionManager()

@router.websocket("/ws/{client_type}")
async def websocket_endpoint(websocket: WebSocket, client_type: Literal["dashboard", "camera"]):
    """
    WebSocket endpoint for real-time communication.
    
    Args:
        client_type: Type of client ('dashboard' or 'camera').
    """
    if client_type not in ["dashboard", "camera"]:
        await websocket.close(code=1003, reason="Invalid client type")
        return
    
    await manager.connect(websocket, client_type)
    
    try:
        await websocket.send_json({
            "type": "connection_established",
            "client_type": client_type,
            "message": f"Connected as {client_type}",
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            # Keep connection alive
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_type)
