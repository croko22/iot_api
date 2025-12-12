import asyncio
import websockets
import json
import uvicorn
import requests
import time
from multiprocessing import Process

URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

async def test_dashboard_client():
    uri = f"{WS_URL}/dashboard"
    print(f"Connecting to {uri}...")
    async with websockets.connect(uri) as websocket:
        # Wait for connection message
        response = await websocket.recv()
        print(f"Dashboard received: {response}")
        
        # Keep listening for sensor update
        print("Dashboard waiting for sensor update...")
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            print(f"Dashboard received ALERT: {response}")
        except asyncio.TimeoutError:
            print("Dashboard timed out waiting for alert.")

async def test_camera_client():
    uri = f"{WS_URL}/camera"
    print(f"Connecting to {uri}...")
    async with websockets.connect(uri) as websocket:
        # Wait for connection message
        response = await websocket.recv()
        print(f"Camera received: {response}")
        
        # Keep listening for alert
        print("Camera waiting for search alert...")
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            print(f"Camera received ALERT: {response}")
        except asyncio.TimeoutError:
            print("Camera timed out waiting for alert.")

def trigger_sensor_update():
    time.sleep(2) # Give clients time to connect
    print("Triggering sensor update with HIGH values...")
    try:
        response = requests.post(f"{URL}/sensors", json={
            "temperature": 60.0,
            "humidity": 30.0,
            "smoke_level": 400.0,
            "timestamp": "2024-01-01T12:00:00"
        })
        print(f"Sensor update response: {response.json()}")
    except Exception as e:
        print(f"Error triggering sensors: {e}")

async def run_tests():
    # Start trigger in separate thread/process simulation
    import threading
    t = threading.Thread(target=trigger_sensor_update)
    t.start()
    
    # Run clients concurrently
    await asyncio.gather(
        test_dashboard_client(),
        test_camera_client()
    )
    t.join()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_tests())
