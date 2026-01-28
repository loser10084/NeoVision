from typing import TypedDict, Annotated, List, Dict, Any, Union
from langchain_core.messages import BaseMessage
import operator

def merge_messages(left: List[BaseMessage], right: Union[BaseMessage, List[BaseMessage]]) -> List[BaseMessage]:
    """保证消息列表正确追加的 reducer"""
    if not isinstance(right, list):
        right = [right]
    return left + right

class AgentState(TypedDict):
    # 1. 核心对话历史 (使用 Annotated 确保消息是追加而非覆盖)
    messages: Annotated[List[BaseMessage], merge_messages]
    
    # 2. 协作控制信号
    # 记录当前是哪个 Agent 在操作 (用于工具执行后精准返回)
    sender: str 
    # Router 指定的下一个 Agent
    next_agent: str
    
    # 3. 业务显式上下文 (显式化有助于 Agent 理解当前状态)
    query: str          # 原始用户问题
    image_url: str      # 图像分析的输入 URL
    
    # RAG 专用上下文：存储最近一次检索出的原始文档，供智能体生成回复时参考
    # 这样可以避免把几千字的文档全部塞进 messages 导致上下文爆炸
    rag_context: List[Dict[str, Any]] 
    web_search_context: List[Dict[str, Any]]
    
    # 图像分析结果预览
    image_analysis_summary: str
    
    # 4. 系统运行统计 (防止死循环)
    step_count: Annotated[int, operator.add]
    
    # 5. 搜索计数限制 (防止搜索死循环)
    search_count: Annotated[int, operator.add]  # 总搜索次数
    consecutive_search_count: Annotated[int, operator.add]  # 连续搜索次数

    # 5. 最终输出 (用于存储最终结果)
    output: str