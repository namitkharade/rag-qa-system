import operator
from typing import Annotated, Optional, Sequence, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


class AgentState(TypedDict):
    """State for the LangGraph agent."""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    query: str
    ephemeral_data: list
    persistent_context: list
    reasoning_steps: list
    final_answer: str
    geometry_analysis: Optional[str]
    revision_count: int
    critique: str
