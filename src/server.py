import asyncio
import json
import logging
from typing import List, Dict

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DigitalTwinServer")

app = FastAPI(title="5G Fronthaul Digital Twin Backend")

# Enable CORS for React frontend (localhost:5173/5174/5175/5176)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        # Store latest operator decisions to sync new clients
        self.current_decisions: Dict = {
            "solutionEnabled": False,
            "slaTarget": 99.999,
            "activeLinkUpgrades": []
        }

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total: {len(self.active_connections)}")
        
        # Send current state immediately upon connection
        await websocket.send_json({
            "type": "INITIAL_STATE",
            "payload": self.current_decisions
        })

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        # Update local state if it's a decision update
        if message.get("type") == "UPDATE_DECISION":
            self.current_decisions.update(message.get("payload", {}))
            
        # Broadcast to all
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "digital-twin-backend"}

@app.get("/results/digital_twin_data.json")
async def get_digital_twin_data():
    """Serve the static data file dynamically."""
    try:
        with open("results/digital_twin_data.json", "r") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        return {"error": "Data not found. Please run the optimizer first."}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            logger.info(f"Received: {data}")
            
            # Echo/Broadcast logic
            # If client sends "UPDATE_DECISION", we broadcast it to everyone else (and back to sender for ack)
            await manager.broadcast(data)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Serve static files (optional, if we built the React app)
# app.mount("/", StaticFiles(directory="digital-twin-ui/dist", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
