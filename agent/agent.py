from typing import List

from config import settings
from geometry_tool import analyze_geometry_tool
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from state import AgentState
from vector_store import vector_store


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


class HybridRAGAgent:
    """
    LangGraph-based agent for hybrid RAG reasoning.
    
    Key behaviors:
    1. Retrieves persistent data from Vector DB (regulatory docs)
    2. Receives ephemeral data at runtime (architectural drawings)
    3. Uses AnalyzeGeometry tool to reason about spatial relationships
    4. Never stores ephemeral data in Vector DB
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0,
            openai_api_key=settings.openai_api_key
        )
        
        # Geometry analysis tool
        self.geometry_tool = analyze_geometry_tool
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build the LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("retrieve", self._retrieve_node)
        workflow.add_node("analyze_ephemeral", self._analyze_ephemeral_node)
        workflow.add_node("reason", self._reason_node)
        workflow.add_node("critique", self._critique_node)
        workflow.add_node("respond", self._respond_node)
        
        # Define edges
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "analyze_ephemeral")
        workflow.add_edge("analyze_ephemeral", "reason")
        workflow.add_edge("reason", "critique")
        
        # Conditional edge after critique
        workflow.add_conditional_edges(
            "critique",
            self._route_after_critique,
            {
                "reason": "reason",  # Loop back for revision
                "respond": "respond"  # Proceed to final response
            }
        )
        
        workflow.add_edge("respond", END)
        
        return workflow.compile()
    
    def _retrieve_node(self, state: AgentState) -> AgentState:
        """
        Retrieve relevant regulatory documents from Vector DB.
        This accesses PERSISTENT data only.
        """
        query = state["query"]
        
        # Search persistent Vector DB
        results = vector_store.similarity_search(query, k=5)
        
        state["persistent_context"] = results
        state["reasoning_steps"].append(
            f"Retrieved {len(results)} regulatory documents from Vector DB"
        )
        
        return state
    
    def _analyze_ephemeral_node(self, state: AgentState) -> AgentState:
        """
        Analyze ephemeral data (architectural drawing JSON).
        This data is NOT retrieved from Vector DB - it's passed at runtime.
        
        Uses the AnalyzeGeometry tool to calculate spatial relationships.
        """
        ephemeral = state.get("ephemeral_data", {})
        
        if ephemeral:
            # Use geometry tool to analyze the drawing
            query = state["query"]
            
            try:
                # Run geometry analysis
                geometry_analysis = self.geometry_tool._run(
                    question=query,
                    drawing_data=ephemeral
                )
                
                # Store the geometry analysis in state
                state["geometry_analysis"] = geometry_analysis
                
                analysis = f"Analyzed ephemeral drawing: Found {len(ephemeral)} objects. Performed geometric analysis."
                state["reasoning_steps"].append(analysis)
                
            except Exception as e:
                error_msg = f"Error analyzing geometry: {str(e)}"
                state["reasoning_steps"].append(error_msg)
                state["geometry_analysis"] = None
        else:
            state["reasoning_steps"].append("No ephemeral data provided for this query")
            state["geometry_analysis"] = None
        
        return state
    
    def _reason_node(self, state: AgentState) -> AgentState:
        """
        Reason over both persistent and ephemeral data.
        Uses geometry analysis results for spatial reasoning.
        
        PRODUCTION-GRADE: Uses with_structured_output() to enforce Pydantic schema,
        eliminating JSON parsing errors that occur ~5-10% with prompt-based approaches.
        """
        # Increment revision count
        revision_count = state.get("revision_count", 0)
        state["revision_count"] = revision_count + 1
        
        query = state["query"]
        persistent = state["persistent_context"]
        ephemeral = state.get("ephemeral_data", {})
        geometry_analysis = state.get("geometry_analysis")
        critique = state.get("critique", "")
        
        # Build context for reasoning
        context_parts = []
        
        if persistent:
            context_parts.append("REGULATORY CONTEXT (from Vector DB):")
            for i, doc in enumerate(persistent[:3], 1):
                context_parts.append(f"{i}. {doc['content'][:300]}...")
        
        if ephemeral and geometry_analysis:
            context_parts.append("\nARCHITECTURAL DRAWING ANALYSIS (ephemeral session data):")
            context_parts.append("The geometry analysis tool has calculated the following:")
            context_parts.append(geometry_analysis)
        elif ephemeral:
            context_parts.append("\nARCHITECTURAL DRAWING (ephemeral session data):")
            context_parts.append(f"Drawing contains {len(ephemeral)} objects")
        
        context = "\n".join(context_parts)
        
        # PRODUCTION FIX: Use structured output with Pydantic schema enforcement
        # This eliminates the ~5-10% JSON parsing failures from "prompt and pray" approach
        structured_llm = self.llm.with_structured_output(ComplianceResult)
        
        # Add critique feedback if this is a revision
        critique_context = ""
        if critique and revision_count > 1:
            critique_context = f"\n\nPREVIOUS CRITIQUE:\nYour previous answer had issues. Please address the following:\n{critique}\n"
        
        prompt = f"""You are a hybrid RAG system analyzing both:
1. Persistent regulatory documents (from Vector DB)
2. Ephemeral architectural drawing data with geometric analysis (from current session)

Your task is to check if the architectural drawing complies with the regulations.

Key regulations to check:
- 50% curtilage rule: Extensions cannot exceed 50% of the plot area
- 2m boundary rule: Structures must be at least 2m from plot boundaries

Query: {query}

Context:
{context}
{critique_context}
Instructions:
1. Provide a comprehensive compliance analysis in the 'answer' field
2. Set 'is_compliant' to true only if ALL regulations are satisfied
3. Support each key finding with at least one citation
4. Citations must reference specific sections/paragraphs from the regulatory documents
5. Include geometric measurements from the drawing analysis in your answer
6. For compliance decisions, cite the exact regulation that was applied"""

        # Invoke with structured output - returns validated ComplianceResult object
        response = structured_llm.invoke([HumanMessage(content=prompt)])
        
        # Convert Pydantic model to dict for JSON serialization
        import json
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
        
        state["reasoning_steps"].append("Completed reasoning with LLM (structured output with Pydantic validation)")
        state["final_answer"] = json.dumps(result_dict, indent=2)
        
        return state
    
    def _respond_node(self, state: AgentState) -> AgentState:
        """
        Final node that prepares the response.
        """
        # Nothing additional to do here - just pass through
        return state
    
    def _critique_node(self, state: AgentState) -> AgentState:
        """
        Critique the final_answer for hallucinations or math errors.
        Reviews the answer against persistent_context and geometry_analysis.
        """
        final_answer = state["final_answer"]
        persistent = state["persistent_context"]
        geometry_analysis = state.get("geometry_analysis")
        revision_count = state.get("revision_count", 0)
        
        # Build context for critique
        context_parts = []
        
        if persistent:
            context_parts.append("REGULATORY DOCUMENTS:")
            for i, doc in enumerate(persistent[:3], 1):
                context_parts.append(f"{i}. {doc['content'][:300]}...")
        
        if geometry_analysis:
            context_parts.append("\nGEOMETRY ANALYSIS:")
            context_parts.append(geometry_analysis)
        
        context = "\n".join(context_parts)
        
        prompt = f"""You are a quality control reviewer. Review the following compliance answer for:
1. Hallucinations: Claims not supported by the regulatory documents
2. Math errors: Incorrect calculations or measurements
3. Logical inconsistencies: Contradictions or unsupported conclusions

ANSWER TO REVIEW:
{final_answer}

SUPPORTING EVIDENCE:
{context}

If the answer is accurate and well-supported, respond with EXACTLY: "Approved"
If there are errors, provide a specific critique explaining what needs to be fixed.
Be concise and direct in your critique."""

        response = self.llm.invoke([HumanMessage(content=prompt)])
        critique = response.content.strip()
        
        state["critique"] = critique
        state["reasoning_steps"].append(f"Critique (revision {revision_count}): {critique[:100]}...")
        
        return state
    
    def _route_after_critique(self, state: AgentState) -> str:
        """
        Conditional routing after critique.
        - If critique is "Approved" or revision_count > 3, go to END
        - Otherwise, go back to reason node to fix the answer
        """
        critique = state.get("critique", "")
        revision_count = state.get("revision_count", 0)
        
        # Check termination conditions
        if "Approved" in critique or revision_count > 3:
            return "respond"
        else:
            return "reason"
    
    def query(self, query: str, ephemeral_data=None):
        """
        Query the agent with both persistent and ephemeral data.
        
        Args:
            query: The user's question
            ephemeral_data: Optional ephemeral data (e.g., architectural drawing JSON)
                           Should be a list of drawing objects
        
        Returns:
            Response with reasoning, sources, and geometry analysis
        """
        initial_state = {
            "messages": [HumanMessage(content=query)],
            "query": query,
            "ephemeral_data": ephemeral_data or {},
            "persistent_context": [],
            "reasoning_steps": [],
            "final_answer": "",
            "geometry_analysis": None,
            "revision_count": 0,
            "critique": ""
        }
        
        # Run the graph
        final_state = self.graph.invoke(initial_state)
        
        return {
            "answer": final_state["final_answer"],
            "reasoning_steps": final_state["reasoning_steps"],
            "sources": final_state["persistent_context"],
            "geometry_analysis": final_state.get("geometry_analysis"),
            "used_ephemeral_data": bool(ephemeral_data),
            "revision_count": final_state.get("revision_count", 0),
            "critique": final_state.get("critique", "")
        }


# Global agent instance
agent = HybridRAGAgent()
