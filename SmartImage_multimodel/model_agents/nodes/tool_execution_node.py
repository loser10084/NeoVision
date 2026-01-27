from langgraph.prebuilt import ToolExecutor, ToolInvocation
from model_agents.tools import rag_search, web_search
from langchain_core.messages import ToolMessage
from utils import logger

def tool_execution_node(state):
    """
    修改点：
    1. 增加 step_count 累加防止逻辑死循环。
    2. 严格校验 tool_call_id。
    3. 优化 RAG 上下文的存储逻辑。
    """
    last_message = state["messages"][-1]
    tool_calls = getattr(last_message, 'tool_calls', [])

    if not tool_calls:
        return {}

    tools = [rag_search, web_search]
    tool_executor = ToolExecutor(tools)
    
    new_tool_messages = []
    current_rag_docs = []
    web_search_context = []

    for tool_call in tool_calls:
        # 记录开始执行
        logger.info(f"--- [TOOL] 执行工具: {tool_call['name']} --- 输入参数: {tool_call['args']}")
        
        action = ToolInvocation(
            tool=tool_call['name'],
            tool_input=tool_call['args']
        )
        
        try:
            result = tool_executor.invoke(action)
            # 如果结果是 List[Document]，提取内容
            content = str(result)
            
            if tool_call['name'] == 'rag_search':
                current_rag_docs = result if isinstance(result, list) else [content]
            if tool_call['name'] == 'web_search':
                web_search_context = result if isinstance(result, list) else [content]
        except Exception as e:
            logger.error(f"工具执行失败: {str(e)}")
            content = f"Error: {str(e)}"

        content = f"参数{tool_call['args']}的{tool_call['name']}结果为： " + content

        # 重点：构建 ToolMessage 必须确保 tool_call_id 与之一一对应
        tool_msg = ToolMessage(
            content=content,
            tool_call_id=tool_call['id'], # 必须匹配，否则 LLM 会认为没执行
            name=tool_call['name']
        )
        new_tool_messages.append(tool_msg)

    # 打印调试信息，确认消息是否生成
    logger.info(f"[tool_execution_node] 已生成 {len(new_tool_messages)} 条回复消息")

    # 计算本次调用中执行的搜索工具数量
    executed_search_count = sum(1 for tc in tool_calls if tc['name'] in ['rag_search', 'web_search'])
    
    return {
        "messages": new_tool_messages,
        "rag_context": current_rag_docs,
        "web_search_context": web_search_context,
        "sender": state.get("sender"), # 明确保持 sender
        "step_count": 1, # 累加步数
        "search_count": executed_search_count,  # 增加搜索次数
        "consecutive_search_count": executed_search_count  # 增加连续搜索次数
    }