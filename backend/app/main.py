import json
# Import schemas from backend root
import sys
from contextlib import asynccontextmanager
from datetime import timedelta
from pathlib import Path
from typing import List

from app.auth import (ACCESS_TOKEN_EXPIRE_MINUTES, Token, User,
                      authenticate_user, create_access_token, get_current_user)
from app.config import settings
from app.redis_client import RedisClient, get_redis_client
from app.routers import agent, chat, session
from fastapi import Body, Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, ValidationError

backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(backend_root))
from schemas import get_drawing_metadata, validate_drawing_json


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Test Redis connection
    try:
        test_client = RedisClient()
        test_client.ping()
        print("✓ Redis connection established")
        test_client.close()
    except Exception as e:
        print(f"⚠ Warning: Redis connection failed: {e}")
    
    yield
    
    # Shutdown: Clean up resources (connections managed per-request)
    print("✓ Application shutdown complete")


app = FastAPI(
    title="Hybrid RAG API",
    description="Backend API for AICI Challenge Hybrid RAG System",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(session.router, prefix="/api/session", tags=["session"])
app.include_router(agent.router, prefix="/api/agent", tags=["agent"])


class UploadDrawingRequest(BaseModel):
    drawing: List[dict]


class UploadDrawingResponse(BaseModel):
    success: bool
    message: str
    user_id: str
    metadata: dict
    ttl_seconds: int


@app.get("/")
async def root():
    return {
        "message": "Hybrid RAG API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check(redis_client: RedisClient = Depends(get_redis_client)):
    redis_status = redis_client.ping()
    return {
        "status": "healthy",
        "redis": "connected" if redis_status else "disconnected"
    }


@app.post("/login", response_model=Token, tags=["authentication"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login, get an access token for future requests.
    
    Args:
        form_data: OAuth2 password request form with username and password
    
    Returns:
        JWT access token
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["user_id"]},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/upload_drawing", response_model=UploadDrawingResponse, tags=["drawing"])
async def upload_drawing(
    request: UploadDrawingRequest = Body(...),
    current_user: User = Depends(get_current_user),
    redis_client: RedisClient = Depends(get_redis_client)
):
    """
    Upload architectural drawing JSON for caching.
    
    This endpoint stores the drawing data in Redis with a 1-hour TTL.
    The data is NOT vector embedded - it's ephemeral and session-specific.
    Uses authenticated user_id from JWT token to prevent IDOR attacks.
    
    Args:
        drawing: List of drawing objects (LINE or POLYLINE)
        current_user: Authenticated user from JWT token (automatic)
    
    Returns:
        Success status, metadata, and TTL information
    """
    try:
        # Validate the drawing JSON using Pydantic schemas
        validated_drawing = validate_drawing_json(request.drawing)
        
        # Extract metadata for response
        metadata = get_drawing_metadata(request.drawing)
        
        # Store in Redis with 1-hour TTL using authenticated user_id
        success = redis_client.store_drawing(
            user_id=current_user.user_id,
            drawing_data=request.drawing,
            ttl=3600  # 1 hour
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to store drawing in Redis cache"
            )
        
        return UploadDrawingResponse(
            success=True,
            message=f"Drawing cached successfully for user {current_user.user_id}",
            user_id=current_user.user_id,
            metadata=metadata,
            ttl_seconds=3600
        )
        
    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid drawing format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing drawing: {str(e)}"
        )


@app.get("/get_drawing", tags=["drawing"])
async def get_drawing(
    current_user: User = Depends(get_current_user),
    redis_client: RedisClient = Depends(get_redis_client)
):
    """
    Retrieve cached drawing data for authenticated user.
    
    Uses authenticated user_id from JWT token to prevent IDOR attacks.
    
    Args:
        current_user: Authenticated user from JWT token (automatic)
    
    Returns:
        Drawing data and remaining TTL
    """
    drawing = redis_client.get_drawing(current_user.user_id)
    
    if drawing is None:
        raise HTTPException(
            status_code=404,
            detail=f"No drawing found for user {current_user.user_id} (may have expired)"
        )
    
    ttl = redis_client.get_ttl(current_user.user_id)
    
    return {
        "user_id": current_user.user_id,
        "drawing": drawing,
        "ttl_seconds": ttl,
        "metadata": get_drawing_metadata(drawing)
    }


@app.delete("/delete_drawing", tags=["drawing"])
async def delete_drawing(
    current_user: User = Depends(get_current_user),
    redis_client: RedisClient = Depends(get_redis_client)
):
    """
    Delete cached drawing data for authenticated user.
    
    Uses authenticated user_id from JWT token to prevent IDOR attacks.
    
    Args:
        current_user: Authenticated user from JWT token (automatic)
    
    Returns:
        Success status
    """
    success = redis_client.delete_drawing(current_user.user_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"No drawing found for user {current_user.user_id}"
        )
    
    return {
        "success": True,
        "message": f"Drawing deleted for user {current_user.user_id}"
    }
