from app.models import SessionCreate, SessionResponse, SessionUpdate
from app.session_manager import session_manager
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/create", response_model=SessionResponse)
async def create_session(session_data: SessionCreate):
    """Create a new session."""
    session = session_manager.create_session(session_data.session_name)
    return session


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get session details."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionResponse(
        session_id=session["session_id"],
        session_name=session["session_name"],
        created_at=session["created_at"],
        ephemeral_data=session.get("ephemeral_data")
    )


@router.post("/update-ephemeral")
async def update_ephemeral_data(update: SessionUpdate):
    """Update ephemeral data for a session."""
    success = session_manager.update_ephemeral_data(
        update.session_id,
        update.ephemeral_data
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Ephemeral data updated successfully"}


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    success = session_manager.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Session deleted successfully"}
