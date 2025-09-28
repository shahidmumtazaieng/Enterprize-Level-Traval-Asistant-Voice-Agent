from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SessionCreate(BaseModel):
    """Schema for creating a new session"""
    system_prompt: str = "You are a friendly travel assistant."
    agent_name: str = "TravelAssistant"
    language: str = "en"

class SessionResponse(BaseModel):
    """Schema for session response"""
    session_id: str
    system_prompt: str
    agent_name: str
    status: str = "created"
    created_at: Optional[datetime] = None
    livekit_room: Optional[str] = None
    livekit_user_token: Optional[str] = None
    livekit_agent_token: Optional[str] = None

class SessionInfo(BaseModel):
    """Schema for session information"""
    session_id: str
    system_prompt: str
    agent_name: str
    status: str
    created_at: datetime
    livekit_room: Optional[str] = None
    livekit_token: Optional[str] = None