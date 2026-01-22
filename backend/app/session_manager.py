import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from app.models import SessionResponse


class SessionManager:
    """Manages ephemeral session data in memory."""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def create_session(self, session_name: Optional[str] = None) -> SessionResponse:
        """Create a new session."""
        session_id = str(uuid.uuid4())
        session_name = session_name or f"Session-{session_id[:8]}"
        
        session_data = {
            "session_id": session_id,
            "session_name": session_name,
            "created_at": datetime.now(),
            "ephemeral_data": None,
            "messages": []
        }
        
        self.sessions[session_id] = session_data
        
        return SessionResponse(
            session_id=session_id,
            session_name=session_name,
            created_at=session_data["created_at"],
            ephemeral_data=None
        )
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data."""
        return self.sessions.get(session_id)
    
    def update_ephemeral_data(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Update ephemeral data for a session."""
        if session_id not in self.sessions:
            return False
        
        self.sessions[session_id]["ephemeral_data"] = data
        return True
    
    def add_message(self, session_id: str, role: str, content: str):
        """Add a message to session history."""
        if session_id in self.sessions:
            self.sessions[session_id]["messages"].append({
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            })
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False


session_manager = SessionManager()
