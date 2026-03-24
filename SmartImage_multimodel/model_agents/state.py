import operator
from typing import Annotated, Any, Dict, List, TypedDict, Union

from langchain_core.messages import BaseMessage


def merge_messages(
    left: List[BaseMessage], right: Union[BaseMessage, List[BaseMessage]]
) -> List[BaseMessage]:
    if not isinstance(right, list):
        right = [right]
    return left + right


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], merge_messages]

    sender: str
    next_agent: str

    query: str
    image_url: str

    rag_context: List[Dict[str, Any]]
    web_search_context: List[Dict[str, Any]]
    image_analysis_summary: str

    step_count: Annotated[int, operator.add]
    search_count: Annotated[int, operator.add]
    consecutive_search_count: int

    output: str
