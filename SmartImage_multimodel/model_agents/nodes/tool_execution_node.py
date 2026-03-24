from langchain_core.messages import ToolMessage
from langgraph.prebuilt import ToolExecutor, ToolInvocation

from model_agents.tools import rag_search, web_search
from utils import logger


def tool_execution_node(state):
    last_message = state["messages"][-1]
    tool_calls = getattr(last_message, "tool_calls", [])
    current_consecutive_search_count = state.get("consecutive_search_count", 0)

    if not tool_calls:
        return {}

    tool_executor = ToolExecutor([rag_search, web_search])
    new_tool_messages = []
    current_rag_docs = []
    web_search_context = []

    for tool_call in tool_calls:
        logger.info(
            f"--- [TOOL] executing: {tool_call['name']} args={tool_call['args']}"
        )
        action = ToolInvocation(
            tool=tool_call["name"],
            tool_input=tool_call["args"],
        )

        try:
            result = tool_executor.invoke(action)
            content = str(result)

            if tool_call["name"] == "rag_search":
                current_rag_docs = result if isinstance(result, list) else [content]
            if tool_call["name"] == "web_search":
                web_search_context = result if isinstance(result, list) else [content]
        except Exception as exc:
            logger.error(f"tool execution failed: {exc}")
            content = f"Error: {exc}"

        tool_msg = ToolMessage(
            content=f"Tool `{tool_call['name']}` result for args {tool_call['args']}: {content}",
            tool_call_id=tool_call["id"],
            name=tool_call["name"],
        )
        new_tool_messages.append(tool_msg)

    logger.info(f"[tool_execution_node] generated {len(new_tool_messages)} replies")

    executed_search_count = sum(
        1 for tool_call in tool_calls if tool_call["name"] in {"rag_search", "web_search"}
    )
    return {
        "messages": new_tool_messages,
        "rag_context": current_rag_docs,
        "web_search_context": web_search_context,
        "sender": state.get("sender"),
        "step_count": 1,
        "search_count": executed_search_count,
        "consecutive_search_count": current_consecutive_search_count + executed_search_count,
    }
