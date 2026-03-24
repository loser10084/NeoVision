from pathlib import Path
from typing import Sequence

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from utils import logger


MAX_TOTAL_SEARCHES = 10
MAX_CONSECUTIVE_SEARCHES = 3


def _load_prompt(prompt_file: str) -> str:
    prompt_path = Path(__file__).parent.parent / prompt_file
    return prompt_path.read_text(encoding="utf-8")


def create_specialized_agent(llm, *, agent_name: str, prompt_file: str, tools: Sequence):
    system_prompt = _load_prompt(prompt_file)

    def agent_node(state):
        current_search_count = state.get("search_count", 0)
        current_consecutive_search_count = state.get("consecutive_search_count", 0)

        if (
            current_search_count >= MAX_TOTAL_SEARCHES
            or current_consecutive_search_count >= MAX_CONSECUTIVE_SEARCHES
        ):
            available_tools = []
            limited_system_prompt = (
                system_prompt
                + "\n\nTool usage is disabled because the search limit has been reached. "
                + "Answer with the existing context only, and clearly note any uncertainty."
            )
        else:
            available_tools = list(tools)
            limited_system_prompt = system_prompt + "\n\nAvailable tools: {tool_names}"

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", limited_system_prompt),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        if available_tools:
            prompt = prompt.partial(
                tool_names=", ".join(tool.name for tool in available_tools)
            )
            chain = prompt | llm.bind_tools(available_tools)
        else:
            prompt = prompt.partial(tool_names="none")
            chain = prompt | llm

        logger.info(f"[{agent_name}] start")
        result = chain.invoke({"messages": state["messages"]})

        updates = {
            "messages": [result],
            "sender": agent_name,
            "step_count": 1,
        }
        if not getattr(result, "tool_calls", None):
            updates["consecutive_search_count"] = 0
        return updates

    return agent_node
