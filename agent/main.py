from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from graph import compliance_graph
from pydantic import BaseModel

app = FastAPI(
    title="Hybrid RAG Agent",
    description="LangGraph-based agent for hybrid RAG reasoning with compliance checking",
    version="1.0.0"
)


class ProcessRequest(BaseModel):
    message: str
    user_id: str  # For fetching drawing from Redis
    session_id: Optional[str] = None


class ProcessResponse(BaseModel):
    answer: str
    regulations: list
    geometry_analysis: Optional[str]
    reasoning_steps: list
    drawing_available: bool


@app.get("/")
async def root():
    return {"message": "Hybrid RAG Agent with Compliance Graph", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/process", response_model=ProcessResponse)
async def process_message(request: ProcessRequest):
    """
    Process a compliance question using the three-node LangGraph workflow.
    
    Workflow:
    1. retrieve_regulations: Query ChromaDB for relevant rules
    2. inspect_drawing: Get measurements from Redis-cached drawing
    3. synthesize: Combine regulations + measurements for answer
    
    Args:
        message: User's compliance question
        user_id: User ID for fetching drawing from Redis
    
    Returns:
        Comprehensive compliance analysis
    """
    try:
        # Process with the graph
        result = compliance_graph.process(
            user_question=request.message,
            user_id=request.user_id
        )
        
        return ProcessResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
