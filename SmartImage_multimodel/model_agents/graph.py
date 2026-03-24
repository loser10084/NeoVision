from langgraph.graph import StateGraph

from utils import logger

from .agents.clinical_guideline_agent import create_clinical_guideline_retrieval_agent
from .agents.imaging_analysis_agent import create_imaging_analysis_agent
from .agents.operation_assistant_agent import create_operation_assistant_agent
from .agents.quality_assessment_agent import create_quality_assessment_agent
from .llm import build_common_llm, build_image_llm
from .nodes import output_node, router_node, tool_execution_node
from .state import AgentState


def create_multi_agent_graph(streaming: bool = False):
    common_llm = build_common_llm(streaming=streaming)
    image_llm = build_image_llm(streaming=streaming)

    quality_assessment_agent = create_quality_assessment_agent(common_llm)
    operation_assistant_agent = create_operation_assistant_agent(common_llm)
    imaging_analysis_agent = create_imaging_analysis_agent(image_llm)
    clinical_guideline_agent = create_clinical_guideline_retrieval_agent(common_llm)

    def should_continue_after_agent(state):
        last_message = state["messages"][-1]
        next_node = (
            "tool_execution"
            if hasattr(last_message, "tool_calls") and last_message.tool_calls
            else "output_handler"
        )
        logger.info(f"[graph] next node: {next_node}")
        return next_node

    workflow = StateGraph(AgentState)

    workflow.add_node("router", router_node)
    workflow.add_node("quality_assessment_agent", quality_assessment_agent)
    workflow.add_node("operation_assistant_agent", operation_assistant_agent)
    workflow.add_node("imaging_analysis_agent", imaging_analysis_agent)
    workflow.add_node("clinical_guideline_retrieval_agent", clinical_guideline_agent)
    workflow.add_node("tool_execution", tool_execution_node)
    workflow.add_node("output_handler", output_node)

    workflow.add_edge("output_handler", "__end__")
    workflow.add_conditional_edges(
        "router",
        lambda x: x.get("next_agent", "operation_assistant_agent"),
        {
            "quality_assessment_agent": "quality_assessment_agent",
            "operation_assistant_agent": "operation_assistant_agent",
            "imaging_analysis_agent": "imaging_analysis_agent",
            "clinical_guideline_retrieval_agent": "clinical_guideline_retrieval_agent",
        },
    )

    for agent_name in (
        "quality_assessment_agent",
        "operation_assistant_agent",
        "imaging_analysis_agent",
        "clinical_guideline_retrieval_agent",
    ):
        workflow.add_conditional_edges(
            agent_name,
            should_continue_after_agent,
            {
                "tool_execution": "tool_execution",
                "output_handler": "output_handler",
            },
        )

    workflow.add_conditional_edges(
        "tool_execution",
        lambda x: x["sender"],
        {
            "quality_assessment_agent": "quality_assessment_agent",
            "operation_assistant_agent": "operation_assistant_agent",
            "imaging_analysis_agent": "imaging_analysis_agent",
            "clinical_guideline_retrieval_agent": "clinical_guideline_retrieval_agent",
        },
    )

    workflow.set_entry_point("router")
    return workflow.compile()
