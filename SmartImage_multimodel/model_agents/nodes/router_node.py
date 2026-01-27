from typing import Any, Dict
from utils import logger

# model_agents/nodes/router_node.py
def router_node(state):
    """
    路由节点：仅返回需要改变的状态字段
    """
    # 1. 逻辑判断
    has_image = bool(state.get("image_url") or state.get("image_urls"))
    
    if not has_image:
        for msg in state.get("messages", []):
            if hasattr(msg, 'content') and isinstance(msg.content, list):
                if any(isinstance(item, dict) and item.get('type') == 'image_url' for item in msg.content):
                    has_image = True
                    break
    
    selected_agent = "image_agent" if has_image else "general_agent"

    # logger为
    # logger.info(f"[router_node] input={state['messages']}, next_agent={selected_agent}")
    # for格式化打印state['messages']最后一条，且若太长，只打印前100个字符
    for msg in state['messages'][-1:]:
        logger.info(f"[router_node] 用户输入={msg.content[:100] if len(msg.content) > 100 else msg.content}")
    logger.info("下一节点" + selected_agent)
    return {
        "next_agent": selected_agent,
        "step_count": 1  # 记录进入了路由步骤
    }