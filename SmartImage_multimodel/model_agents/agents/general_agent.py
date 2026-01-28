# model_agents/agents/general_agent.py
from utils import logger
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import os
from pathlib import Path


def create_general_agent(llm):
    """
    创建普通对话智能体（函数式）
    """
    # 读取系统提示词
    system_prompt_path = Path(__file__).parent.parent / "system_prompt.md"
    with open(system_prompt_path, 'r', encoding='utf-8') as f:
        system_prompt = f.read()

    def general_agent_node(state):
        """
        普通对话节点
        """
        from model_agents.tools.rag_search_tool import rag_search
        from model_agents.tools.web_search_tool import web_search
        
        # 检查搜索次数限制，防止死循环
        max_total_searches = 10  # 总搜索次数上限
        max_consecutive_searches = 3  # 连续搜索次数上限
        
        current_search_count = state.get("search_count", 0)
        current_consecutive_search_count = state.get("consecutive_search_count", 0)
        
        # 根据搜索次数决定是否绑定搜索工具
        all_tools = [rag_search, web_search]
        
        # 如果搜索次数已达上限，则不绑定搜索工具
        if current_search_count >= max_total_searches or current_consecutive_search_count >= max_consecutive_searches:
            tools = []  # 不绑定任何工具
            # 更新系统提示，告知智能体无法使用搜索工具
            limited_system_prompt = system_prompt + f"\n\n注意：由于已达到搜索次数限制（总搜索次数：{max_total_searches}，连续搜索次数：{max_consecutive_searches}），当前无法使用搜索工具。请基于现有信息回答问题。"
        else:
            tools = all_tools
            limited_system_prompt = system_prompt + "\n\nUse the available tools: {tool_names}"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", limited_system_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ])
        
        if tools:
            prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
            chain = prompt | llm.bind_tools(tools)
        else:
            prompt = prompt.partial(tool_names="无可用工具")
            chain = prompt | llm
        
        # 执行智能体
        # logger.info(f"[general_agent_node] input={state['messages']}")
        logger.info("开始执 [general_agent_node]")
        result = chain.invoke(state["messages"])
        logger.debug(f"[general_agent_node] result={result}")
    
        # 计算本次调用中使用的搜索工具数量
        search_tool_usage = 0
        if hasattr(result, 'tool_calls') and result.tool_calls:
            search_tool_usage = sum(1 for tc in result.tool_calls if tc['name'] in ['rag_search', 'web_search'])
    
        return {
            "messages": [result], # merge_messages 会处理追加
            "sender": "general_agent", # 声明身份
            "step_count": 1, # 自动累加
            "search_count": search_tool_usage,  # 增加搜索次数
            "consecutive_search_count": search_tool_usage  # 增加连续搜索次数
        }

    return general_agent_node