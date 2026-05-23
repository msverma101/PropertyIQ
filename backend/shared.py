import os
from typing import Dict, List, Any
from fastapi import WebSocket
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

ASYNC_DB_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "database.db")
)
DATABASE_URL_ASYNC = f"sqlite+aiosqlite:///{ASYNC_DB_FILE}"

async_engine = create_async_engine(DATABASE_URL_ASYNC, echo=False)
async_session_maker = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

# In-memory mapping to track caller info per call_id
active_call_sessions: Dict[str, Dict[str, Any]] = {}

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, call_id: str, websocket: WebSocket):
        await websocket.accept()
        if call_id not in self.active_connections:
            self.active_connections[call_id] = []
        self.active_connections[call_id].append(websocket)

    def disconnect(self, call_id: str, websocket: WebSocket):
        if call_id in self.active_connections:
            if websocket in self.active_connections[call_id]:
                self.active_connections[call_id].remove(websocket)
            if not self.active_connections[call_id]:
                del self.active_connections[call_id]

    async def broadcast(self, call_id: str, message: dict):
        if call_id in self.active_connections:
            for connection in self.active_connections[call_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass
        if call_id != "all" and "all" in self.active_connections:
            for connection in self.active_connections["all"]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

manager = ConnectionManager()
