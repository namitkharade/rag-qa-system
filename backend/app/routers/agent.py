"""Agent proxy router that forwards requests to the agent service."""
from typing import Any, Dict, List, Optional

import httpx
from app.config import settings
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class AgentProcessRequest(BaseModel):
    message: str
    user_id: str
    session_id: Optional[str] = None


class AgentProcessResponse(BaseModel):
    answer: str
    regulations: List[Dict[str, Any]]
    geometry_analysis: Optional[str]
    reasoning_steps: List[str]
    drawing_available: bool


@router.post("/process", response_model=AgentProcessResponse)
async def process_with_agent(request: AgentProcessRequest):
    """Proxy request to the agent service."""
    try:
        agent_host = getattr(settings, 'agent_host', 'localhost')
        agent_port = getattr(settings, 'agent_port', 8002)
        agent_url = f"http://{agent_host}:{agent_port}/process"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                agent_url,
                json={
                    "message": request.message,
                    "user_id": request.user_id,
                    "session_id": request.session_id
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Agent service error: {response.text}"
                )
            
            return response.json()
    
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Agent service timeout - processing took too long"
        )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Agent service unavailable - cannot connect"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error communicating with agent: {str(e)}"
        )


@router.get("/health")
async def agent_health_check():
    """Check if the agent service is reachable."""
    try:
        agent_host = getattr(settings, 'agent_host', 'localhost')
        agent_port = getattr(settings, 'agent_port', 8002)
        agent_url = f"http://{agent_host}:{agent_port}/health"
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(agent_url)
            
            return {
                "agent_status": "healthy" if response.status_code == 200 else "unhealthy",
                "agent_url": agent_url,
                "response": response.json() if response.status_code == 200 else None
            }
    
    except Exception as e:
        return {
            "agent_status": "unreachable",
            "error": str(e)
        }
