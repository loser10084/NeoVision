from model_agents.tools.rag_search_tool import rag_search
from model_agents.tools.web_search_tool import web_search

from .base import create_specialized_agent


def create_clinical_guideline_retrieval_agent(llm):
    return create_specialized_agent(
        llm,
        agent_name="clinical_guideline_retrieval_agent",
        prompt_file="clinical_guideline_system_prompt.md",
        tools=[rag_search, web_search],
    )
