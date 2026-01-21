"""
LangGraph workflow for Hybrid RAG compliance checking.

This graph implements a three-stage workflow:
1. retrieve_regulations: Query ChromaDB for relevant rules
2. inspect_drawing: Analyze geometry from Redis-cached JSON
3. synthesize: Combine regulations + measurements to answer user
"""

import json
import operator
from typing import Annotated, Any, Dict, List, Optional, Sequence, TypedDict

import redis
from config import settings
from geometry_tool import AnalyzeGeometryTool
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from vector_store import VectorStore


# Structured output schemas for production-grade LLM responses
class Citation(BaseModel):
    """Schema for a single citation reference."""
    source: str = Field(description="Document/Regulation name")
    reference: str = Field(description="Specific paragraph, section, or page number")
    content: str = Field(description="Exact quote or paraphrase from the source")
    relevance: str = Field(description="Brief explanation of how this citation supports the answer")


class ComplianceResult(BaseModel):
    """Schema for compliance check result with strict validation."""
    answer: str = Field(description="The final compliance check answer with detailed findings")
    is_compliant: bool = Field(description="Whether the design complies with regulations")
    citations: List[Citation] = Field(description="References to regulatory documents with specific sections")


class GraphState(TypedDict):
    """
    State for the LangGraph compliance checking workflow.
    
    This state flows through all three nodes, accumulating context:
    1. User question and drawing reference
    2. Retrieved regulations from ChromaDB
    3. Geometric measurements from AnalyzeGeometry tool
    4. Final synthesized answer
    """
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_question: str
    user_id: str  # For fetching drawing from Redis
    
    # Retrieved from ChromaDB
    regulations: List[Dict[str, Any]]
    
    # Analyzed from drawing
    drawing_data: Optional[List[Dict[str, Any]]]
    geometry_analysis: Optional[str]
    
    # Final output
    final_answer: str
    reasoning_steps: List[str]


class HybridRAGGraph:
    """
    LangGraph implementation for hybrid RAG compliance checking.
    
    Workflow:
        user_question + user_id
              ↓
        retrieve_regulations (ChromaDB query)
              ↓
        inspect_drawing (AnalyzeGeometry + Redis)
              ↓
        synthesize (LLM combines both contexts)
              ↓
        final_answer
    """
    
    def __init__(self):
        # LLM for synthesis
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0,
            openai_api_key=settings.openai_api_key
        )
        
        # Vector store for regulations
        self.vector_store = VectorStore()
        
        # Geometry analysis tool
        self.geometry_tool = AnalyzeGeometryTool()
        
        # Redis client for fetching drawings
        self.redis_client = redis.Redis(
            host=getattr(settings, 'redis_host', 'localhost'),
            port=getattr(settings, 'redis_port', 6379),
            db=getattr(settings, 'redis_db', 0),
            decode_responses=True
        )
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the three-node LangGraph workflow."""
        workflow = StateGraph(GraphState)
        
        # Add nodes
        workflow.add_node("retrieve_regulations", self._retrieve_regulations_node)
        workflow.add_node("inspect_drawing", self._inspect_drawing_node)
        workflow.add_node("synthesize", self._synthesize_node)
        
        # Define edges (linear flow)
        workflow.set_entry_point("retrieve_regulations")
        workflow.add_edge("retrieve_regulations", "inspect_drawing")
        workflow.add_edge("inspect_drawing", "synthesize")
        workflow.add_edge("synthesize", END)
        
        return workflow.compile()
    
    def _retrieve_regulations_node(self, state: GraphState) -> GraphState:
        """Retrieve relevant regulations from ChromaDB."""
        question = state["user_question"]
        
        state["reasoning_steps"].append(
            f"Querying ChromaDB for regulations related to: '{question}'"
        )
        
        results = self.vector_store.similarity_search(question, k=5)
        
        state["regulations"] = results
        state["reasoning_steps"].append(
            f"Retrieved {len(results)} relevant regulatory documents"
        )
        
        return state
    
    def _inspect_drawing_node(self, state: GraphState) -> GraphState:
        """Fetch drawing from Redis and run geometric analysis."""
        user_id = state["user_id"]
        question = state["user_question"]
        
        state["reasoning_steps"].append(
            f"Fetching drawing for user: {user_id}"
        )
        
        try:
            key = f"session:{user_id}:drawing"
            json_str = self.redis_client.get(key)
            
            if json_str:
                drawing_data = json.loads(json_str)
                state["drawing_data"] = drawing_data
                
                state["reasoning_steps"].append(
                    f"Retrieved drawing with {len(drawing_data)} objects"
                )
                
                state["reasoning_steps"].append(
                    "Running geometric analysis"
                )
                
                geometry_analysis = self.geometry_tool._run(
                    question=question,
                    drawing_data=drawing_data
                )
                
                state["geometry_analysis"] = geometry_analysis
                state["reasoning_steps"].append(
                    "Geometric analysis complete"
                )
            else:
                state["drawing_data"] = None
                state["geometry_analysis"] = None
                state["reasoning_steps"].append(
                    "No drawing found in Redis (may have expired)"
                )
        
        except Exception as e:
            state["drawing_data"] = None
            state["geometry_analysis"] = None
            state["reasoning_steps"].append(
                f"Error fetching/analyzing drawing: {str(e)}"
            )
        
        return state
    
    def _synthesize_node(self, state: GraphState) -> GraphState:
        """Synthesize final answer using LLM with structured output."""
        question = state["user_question"]
        regulations = state["regulations"]
        geometry_analysis = state.get("geometry_analysis")
        
        state["reasoning_steps"].append(
            "Synthesizing answer from regulations and measurements"
        )
        
        prompt_parts = [
            "You are a regulatory compliance assistant analyzing architectural drawings.",
            "",
            f"USER QUESTION: {question}",
            "",
            "=" * 80,
            "CONTEXT 1: RELEVANT REGULATIONS (from ChromaDB)",
            "=" * 80,
        ]
        
        if regulations:
            for i, doc in enumerate(regulations, 1):
                prompt_parts.append(f"\nRegulation {i}:")
                prompt_parts.append(f"Source: {doc.get('metadata', {}).get('source_name', 'Unknown')}")
                prompt_parts.append(f"Relevance Score: {doc.get('score', 'N/A')}")
                prompt_parts.append(f"Content: {doc['content'][:500]}...")
                prompt_parts.append("-" * 80)
        else:
            prompt_parts.append("\nNo regulations retrieved from database.")
        
        prompt_parts.append("\n" + "=" * 80)
        prompt_parts.append("CONTEXT 2: GEOMETRIC MEASUREMENTS (from AnalyzeGeometry)")
        prompt_parts.append("=" * 80)
        
        if geometry_analysis:
            prompt_parts.append(geometry_analysis)
        else:
            prompt_parts.append("\nNo drawing data available for analysis.")
        
        prompt_parts.append("\n" + "=" * 80)
        prompt_parts.append("INSTRUCTIONS")
        prompt_parts.append("=" * 80)
        prompt_parts.append("""
Based on the regulations and geometric measurements above, analyze compliance.

Requirements:
1. ANALYZE COMPLIANCE: Check if the drawing complies with relevant regulations
2. SET is_compliant: true only if ALL regulations are satisfied, false otherwise
3. CITE SPECIFIC RULES: Each finding must be supported by at least one citation referencing exact regulations by name/section
4. PROVIDE MEASUREMENTS: Use the exact areas, distances, and percentages from the analysis
5. BE PRECISE: State specific violations or confirmations of compliance
6. EXPLAIN REASONING: Show how regulations apply to the measurements

KEY REGULATIONS TO CHECK:
- 50% curtilage rule: Building/extensions cannot exceed 50% of plot area
- 2m boundary rule: Structures must be at least 2m from plot boundaries
- Height restrictions
- Setback requirements

If data is missing, clearly state what additional information is needed in the answer field.
""")
        
        full_prompt = "\n".join(prompt_parts)
        
        structured_llm = self.llm.with_structured_output(ComplianceResult)
        
        response = structured_llm.invoke([HumanMessage(content=full_prompt)])
        
        result_dict = {
            "answer": response.answer,
            "is_compliant": response.is_compliant,
            "citations": [
                {
                    "source": citation.source,
                    "reference": citation.reference,
                    "content": citation.content,
                    "relevance": citation.relevance
                }
                for citation in response.citations
            ]
        }
        
        state["final_answer"] = json.dumps(result_dict, indent=2)
        state["reasoning_steps"].append(
            "Synthesis complete - answer generated with structured output"
        )
        
        return state
    
    def process(
        self,
        user_question: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Execute the full workflow.
        
        Args:
            user_question: The user's question about compliance
            user_id: User ID for fetching drawing from Redis
        
        Returns:
            Dictionary with answer, regulations, measurements, and reasoning
        """
        # Initialize state
        initial_state = {
            "messages": [HumanMessage(content=user_question)],
            "user_question": user_question,
            "user_id": user_id,
            "regulations": [],
            "drawing_data": None,
            "geometry_analysis": None,
            "final_answer": "",
            "reasoning_steps": []
        }
        
        # Run the graph
        final_state = self.graph.invoke(initial_state)
        
        # Return comprehensive result
        return {
            "answer": final_state["final_answer"],
            "regulations": final_state["regulations"],
            "geometry_analysis": final_state.get("geometry_analysis"),
            "reasoning_steps": final_state["reasoning_steps"],
            "drawing_available": final_state["drawing_data"] is not None
        }


# Global graph instance
compliance_graph = HybridRAGGraph()


def check_compliance(user_question: str, user_id: str) -> Dict[str, Any]:
    """
    Convenience function to check compliance.
    
    Args:
        user_question: Question about regulatory compliance
        user_id: User ID for fetching drawing from Redis
    
    Returns:
        Comprehensive compliance analysis
    """
    return compliance_graph.process(user_question, user_id)


if __name__ == "__main__":
    """
    Test the graph with a sample query.
    """
    import sys
    
    print("\n" + "=" * 80)
    print("HYBRID RAG COMPLIANCE GRAPH - TEST")
    print("=" * 80)
    
    # Sample question
    question = "Does this building extension comply with the 50% curtilage rule and the 2m boundary rule?"
    user_id = "test_user"
    
    print(f"\nQuestion: {question}")
    print(f"User ID: {user_id}")
    print("\nNote: Make sure Redis is running and has drawing data for this user.\n")
    
    try:
        result = check_compliance(question, user_id)
        
        print("\n" + "=" * 80)
        print("REASONING STEPS")
        print("=" * 80)
        for step in result["reasoning_steps"]:
            print(f"  {step}")
        
        print("\n" + "=" * 80)
        print("REGULATIONS FOUND")
        print("=" * 80)
        print(f"  Count: {len(result['regulations'])}")
        
        print("\n" + "=" * 80)
        print("GEOMETRY ANALYSIS")
        print("=" * 80)
        if result["geometry_analysis"]:
            print(result["geometry_analysis"][:500] + "...")
        else:
            print("  No geometry analysis available")
        
        print("\n" + "=" * 80)
        print("FINAL ANSWER")
        print("=" * 80)
        print(result["answer"])
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
