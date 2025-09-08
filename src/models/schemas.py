from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class MessageRequest(BaseModel):
    message: str
    user_id: Optional[str] = None

class MessageResponse(BaseModel):
    id: str
    message: str
    response: str
    timestamp: datetime
    user_id: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str

class StatsResponse(BaseModel):
    total_messages: int
    server_uptime: str
    timestamp: datetime
