from model_agents.tools.rag_search_tool import rag_search
from model_agents.tools.web_search_tool import web_search

from .base import create_specialized_agent


def create_quality_assessment_agent(llm):
    return create_specialized_agent(
        llm,
        agent_name="quality_assessment_agent",
        prompt_file="quality_assessment_system_prompt.md",
        tools=[rag_search, web_search],
    )
