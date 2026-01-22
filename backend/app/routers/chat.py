import httpx
from app.config import settings
from app.models import ChatRequest, ChatResponse
from app.session_manager import session_manager
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Send a message to the AI agent.
    Passes ephemeral data (if available) to the agent at runtime.
    """
    # Verify session exists
    session = session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Add user message to session history
    session_manager.add_message(request.session_id, "user", request.message)
    
    # Prepare context for agent
    # Include ephemeral data from session (architectural drawings)
    context = request.context or {}
    user_id = request.session_id  # Use session_id as user_id for Redis lookups
    
    if session.get("ephemeral_data"):
        context["ephemeral_data"] = session["ephemeral_data"]
    
    try:
        # Call agent service via HTTP
        async with httpx.AsyncClient(timeout=30.0) as client:
            agent_url = f"http://{settings.agent_host}:{settings.agent_port}/process"
            
            response = await client.post(
                agent_url,
                json={
                    "message": request.message,
                    "user_id": user_id,
                    "session_id": request.session_id
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Agent service error: {response.text}"
                )
            
            agent_response = response.json()
        
        # Extract regulations as sources
        sources = []
        if agent_response.get("regulations"):
            for reg in agent_response["regulations"]:
                sources.append({
                    "document": reg.get("source", "unknown"),
                    "relevance": reg.get("relevance", 0.8),
                    "content": reg.get("content", "")
                })
        
        # Parse the structured answer from agent (it's a JSON string)
        import json
        try:
            answer_data = json.loads(agent_response.get("answer", "{}"))
        except json.JSONDecodeError:
            # Fallback if answer is not JSON
            answer_data = {"answer": agent_response.get("answer", "")}
        
        # Add reasoning steps to the structured response
        if agent_response.get("reasoning_steps"):
            answer_data["reasoning_steps"] = agent_response["reasoning_steps"]
        
        if agent_response.get("geometry_analysis"):
            answer_data["geometry_analysis"] = agent_response["geometry_analysis"]
        
        # Store the complete structured response as JSON string
        full_message = json.dumps(answer_data, indent=2)
        
        # Add assistant message to session history
        session_manager.add_message(
            request.session_id,
            "assistant",
            full_message
        )
        
        return ChatResponse(
            session_id=request.session_id,
            message=full_message,
            sources=sources if sources else None,
            metadata={
                "has_ephemeral_data": session.get("ephemeral_data") is not None,
                "drawing_available": agent_response.get("drawing_available", False),
                "reasoning_steps_count": len(agent_response.get("reasoning_steps", []))
            }
        )
        
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Agent service unavailable. Ensure agent container is running."
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Agent service timeout. Please try again."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    """Get chat history for a session."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"messages": session.get("messages", [])}
