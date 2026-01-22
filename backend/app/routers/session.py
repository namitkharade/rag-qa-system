from app.models import SessionCreate, SessionResponse, SessionUpdate
from app.redis_client import RedisClient
from app.session_manager import session_manager
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()


def get_redis_client() -> RedisClient:
    """FastAPI dependency that provides a Redis client instance."""
    return RedisClient()


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
async def update_ephemeral_data(
    update: SessionUpdate,
    redis_client: RedisClient = Depends(get_redis_client)
):
    """
    Update ephemeral data for a session.
    Also stores drawing data in Redis so the agent can access it.
    """
    success = session_manager.update_ephemeral_data(
        update.session_id,
        update.ephemeral_data
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Store ephemeral data in Redis for the agent to access
    # The agent expects the drawing data with key session:{user_id}:drawing
    if update.ephemeral_data:
        try:
            # Check if ephemeral_data has a 'drawing' field or if it IS the drawing
            if isinstance(update.ephemeral_data, dict):
                drawing_data = update.ephemeral_data.get("drawing")
                # If no 'drawing' field, assume the whole object is the drawing
                if not drawing_data:
                    drawing_data = update.ephemeral_data
            elif isinstance(update.ephemeral_data, list):
                # If it's a list, assume it's the drawing data directly
                drawing_data = update.ephemeral_data
            else:
                drawing_data = None
            
            if drawing_data:
                # Store in Redis with session_id as user_id (agent uses this)
                redis_client.store_drawing(
                    user_id=update.session_id,
                    drawing_data=drawing_data,
                    ttl=3600  # 1 hour TTL
                )
        except Exception:
            # Silently fail - don't break the session update
            pass
    
    return {"message": "Ephemeral data updated successfully"}


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    success = session_manager.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Session deleted successfully"}
