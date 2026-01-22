from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime = datetime.now()


class ChatRequest(BaseModel):
    session_id: str
    message: str
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    session_id: str
    message: str
    sources: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


class SessionCreate(BaseModel):
    session_name: Optional[str] = None


class SessionResponse(BaseModel):
    session_id: str
    session_name: str
    created_at: datetime
    ephemeral_data: Optional[Dict[str, Any]] = None


class SessionUpdate(BaseModel):
    session_id: str
    ephemeral_data: Any  # Can be dict, list, or any other JSON type
