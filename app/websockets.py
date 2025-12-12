from fastapi import WebSocket
from typing import List

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
