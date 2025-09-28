from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class ConversationMessage(BaseModel):
    """Schema for a conversation message"""
    id: str
    session_id: str
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

class ConversationTurn(BaseModel):
    """Schema for a conversation turn (user + assistant response)"""
    id: str
    session_id: str
    user_message: ConversationMessage
    assistant_message: Optional[ConversationMessage] = None
    timestamp: datetime
    duration: Optional[float] = None

class ConversationHistory(BaseModel):
    """Schema for conversation history"""
    session_id: str
    turns: List[ConversationTurn]
    total_turns: int
    started_at: datetime
    ended_at: Optional[datetime] = None