from attr import has
from langgraph.graph import StateGraph
from .state import AgentState
from .llm import build_common_llm, build_image_llm
from .agents.general_agent import create_general_agent
from .agents.image_agent import create_image_agent
from .nodes import router_node, tool_execution_node, output_node
from utils import logger


def create_multi_agent_graph(streaming: bool = False):
    common_llm = build_common_llm(streaming=streaming)
    image_llm = build_image_llm(streaming=streaming)
    
    general_agent = create_general_agent(common_llm)
    image_agent = create_image_agent(image_llm)
    

    def should_continue_after_agent(state):
        """
        判断智能体是否需要继续执行（例如，如果有待处理的工具调用）
        """
        last_message = state["messages"][-1]

        next_node = hasattr(last_message, 'tool_calls') and last_message.tool_calls and "tool_execution" or "output_handler"    
        logger.info(f"下一个节点: {next_node}")
        return next_node



    workflow = StateGraph(AgentState)

    workflow.add_node("router", router_node)
    workflow.add_node("general_agent", general_agent)
    workflow.add_node("image_agent", image_agent)
    workflow.add_node("tool_execution", tool_execution_node)
    workflow.add_node("output_handler", output_node)
    
    # bian
    workflow.add_edge("output_handler", "__end__")
    workflow.add_conditional_edges(
        "router",
        lambda x: x.get("next_agent", "general_agent"),
        {
            "general_agent": "general_agent",
            "image_agent": "image_agent"
        }
    )

    # 为general_agent和image_agent添加条件边，检查是否需要执行工具
    workflow.add_conditional_edges(
        "general_agent",
        should_continue_after_agent,
        {
            "tool_execution": "tool_execution",
            "output_handler": "output_handler"
        }
    )

    workflow.add_conditional_edges(
        "image_agent",
        should_continue_after_agent,
        {
            "tool_execution": "tool_execution",
            "output_handler": "output_handler"
        }
    )

    # 工具执行完成后，回到相应的智能体节点
    workflow.add_conditional_edges(
        "tool_execution",
        lambda x: x["sender"],
        {
            "general_agent": "general_agent",
            "image_agent": "image_agent"
        }
    )

    workflow.set_entry_point("router")

    compiled_graph = workflow.compile()
    
    # 为了支持流式输出，我们可以访问编译后的图的流式功能
    return compiled_graph