# api_gateway/agent_runtime.py
# Agent Runtime模块适配器 - 连接API网关与重构后的模型端

from api_gateway.utils.history import load_history_for_model_state
from api_gateway.utils.history import save_history_from_model_state
from model_agents import create_multi_agent_graph
from model_agents.state import AgentState
from langchain_core.messages import HumanMessage, SystemMessage, message_to_dict, messages_from_dict
from langchain.schema import HumanMessage
from utils import logger
from api_gateway.utils import history
import config
from typing import Generator, Dict, Any



# 包装图以匹配原接口
class GraphExecutor:
    def __init__(self, graph, user_id):
        self.graph = graph
        self.user_id = user_id
            
    def invoke(self, inputs, config=None):
        """
        调用执行器
        
        Args:
            inputs: 输入数据，如 {"input": query}
            config: 配置参数
        """
        query = inputs.get("input", "")
        image_url = inputs.get("image_url", None)
        
        # 加载历史消息
        history_messages = load_history_for_model_state(self.user_id)
            
        # 构建初始状态，包含历史消息
        initial_state = {
            "messages": history_messages + [HumanMessage(content=query)],
            "query": query,
            "image_url": image_url,
            "rag_context": [],
            "web_search_context": [],
            "image_analysis_summary": "",
            "step_count": 0,
            "search_count": 0,
            "consecutive_search_count": 0,
            "output": "",
            "next_agent": "router",
            "sender": "general_agent"
        }
            
        # 执行图
        result = self.graph.invoke(initial_state)
            
        # 保存最终状态到历史记录
        save_history_from_model_state(self.user_id, result)
            
        # 提取输出内容
        output = ""
        if hasattr(result, 'get'):
            output = result.get("output", "")
            if not output and "messages" in result:
                # 从消息中获取最新AI回复
                messages = result.get("messages", [])
                if messages:
                    last_msg = messages[-1]
                    if hasattr(last_msg, 'content'):
                        output = last_msg.content
        else:
            output = str(result)
                
        return {"output": output}
            
    def stream(self, inputs, config=None):
        """
            流式调用执行器
            
        Args:
            inputs: 输入数据，如 {"input": query}
            config: 配置参数
        """
        from langchain_core.callbacks import BaseCallbackHandler
        from queue import Queue
        import threading
            
        query = inputs.get("input", "")
            
        # 加载历史消息
        history_messages = load_history_for_model_state(self.user_id)
            
        # 构建初始状态，包含历史消息
        initial_state = {
            "messages": history_messages + [HumanMessage(content=query)],
            "query": query,
            "image_url": None,
            "rag_context": [],
            "web_search_context": [],
            "image_analysis_summary": "",
            "step_count": 0,
            "search_count": 0,
            "consecutive_search_count": 0,
            "output": "",
            "next_agent": "router",
            "sender": "general_agent"
        }
            
        # 创建队列用于收集token
        token_queue = Queue()
            
        # 定义一个回调处理器来捕获token输出
        class TokenStreamingCallbackHandler(BaseCallbackHandler):
            def __init__(self, token_queue):
                self.token_queue = token_queue
                
            def on_llm_new_token(self, token: str, **kwargs) -> None:
                if token:
                    # logger.critical(f"收到token: {token}")
                    self.token_queue.put(token)
                
            def on_tool_start(self, serialized, input_str, **kwargs) -> None:
                # 当工具开始运行时，发送提示信息
                tool_name = serialized.get("name", "unknown") if isinstance(serialized, dict) else "unknown"
                self.token_queue.put(f"\n[正在使用工具: {tool_name}]\n")
                
            def on_tool_end(self, output, **kwargs) -> None:
                # 当工具结束运行时，发送结束提示
                self.token_queue.put("[工具执行完成]\n")
            
        # 添加回调处理器到配置
        if config is None:
            config = {}
            
        # 创建回调处理器实例
        callback_handler = TokenStreamingCallbackHandler(token_queue)
            
        # 将回调处理器添加到config中
        if "callbacks" in config:
            config["callbacks"].append(callback_handler)
        else:
            config["callbacks"] = [callback_handler]
            
        # 首先yield初始状态
        yield {"input": query, "status": "starting"}
            
        # 在单独的线程中运行图的流式处理，以便同时监听token
        def run_graph():
            try:
                # 执行流式处理
                for event in self.graph.stream(initial_state, config=config):
                    # 将事件放入队列，标记为非token数据
                    token_queue.put(("event", event))
            except Exception as e:
                token_queue.put(("error", str(e)))
            finally:
                # 发送结束信号
                token_queue.put(("done", None))
            
        # 启动图执行线程
        graph_thread = threading.Thread(target=run_graph)
        graph_thread.daemon = True
        graph_thread.start()
            
        # 监听来自图执行或token回调的数据
        while True:
            try:
                item = token_queue.get(timeout=30)  # 30秒超时
                
                if isinstance(item, tuple) and len(item) == 2:
                    item_type, data = item
                    if item_type == "event":
                        yield data
                    elif item_type == "error":
                        yield {"error": data}
                        break
                    elif item_type == "done":
                        break
                else:
                    # 假设这是单个token或文本片段
                    token = item
                    if token is not None:
                        # 发送token作为流式输出的一部分
                        yield {"token": token, "type": "token_stream"}
                            
            except:
                # 超时或其他异常，退出循环
                break




# 创建模拟内存对象
class MockMemory:
    """
    模拟原有的memory对象，保持API兼容性
    """
    def __init__(self, user_id: str):
        self.chat_memory = []
        self.user_id = user_id
        
    def save_context(self, inputs, outputs):
        """模拟保存上下文"""
        from utils.history import append_exchange
        user_input = inputs.get("input", "") if isinstance(inputs, dict) else str(inputs)
        output_text = outputs.get("output", "") if isinstance(outputs, dict) else str(outputs)
        append_exchange(self.user_id, user_input, output_text)
        
    def clear(self):
        """清空内存"""
        self.chat_memory = []
    

# 非流式处理版本
def build_agent_executor(user_id: str, provided_messages=None, streaming: bool = False):
    """
    构建智能体执行器 - 与原接口兼容
    
    Args:
        user_id: 用户ID
        provided_messages: 提供的消息列表
        streaming: 是否流式处理
        
    Returns:
        tuple: (executor, memory) - 执行器和内存对象
    """
    # 创建智能体图
    logger.critical(f"创建多模态智能体执行器 - 用户ID: {user_id}")
    graph = create_multi_agent_graph(streaming=streaming)
    
    memory = MockMemory(user_id)
    
    
    executor = GraphExecutor(graph, user_id)
    return executor, memory

def build_multimodal_agent_executor(user_id: str, query: str, image_url: str, streaming: bool = False):
    """
    构建多模态智能体执行器 - 用于处理图像输入
    
    Args:
        user_id: 用户ID
        query: 查询文本
        image_url: 图像URL
        streaming: 是否流式处理
        
    Returns:
        dict: 包含处理结果的字典
    """
    # 创建智能体图
    graph = create_multi_agent_graph(streaming=streaming)
    
    # 加载历史消息
    history_messages = load_history_for_model_state(user_id)
    

    # 构建包含图像的多模态消息
    logger.info(f"构建多模态智能体执行器 - 用户ID: {user_id}, 查询: {query}, 图像URL: {image_url}")
    content_parts = []
    if query:
        content_parts.append({"type": "text", "text": query})
    if image_url:
        content_parts.append({"type": "image_url", "image_url": {"url": image_url}})
    
    # 创建人类消息，包含文本和图像
    from langchain_core.messages import HumanMessage
    human_message = HumanMessage(content=content_parts)
    logger.info(f"创建人类消息 - 内容: {content_parts}")
    
    # 构建初始状态，包含图像信息
    initial_state = {
        "messages": history_messages + [human_message],
        "query": query,
        "image_url": image_url,
        "rag_context": [],
        "web_search_context": [],
        "image_analysis_summary": "",
        "step_count": 0,
        "search_count": 0,
        "consecutive_search_count": 0,
        "output": "",
        "next_agent": "router",  # 这将触发路由节点决定使用哪个智能体
        "sender": "general_agent"
    }
    
    # 执行图
    result = graph.invoke(initial_state)
    
    # 在保存历史记录前，先处理消息内容以避免保存完整的图像URL
    # 这里我们使用history模块的处理函数来清理图像URL
    from api_gateway.utils.history import _process_content_for_storage
    
    # 如果结果包含消息，处理其中的内容
    if "messages" in result:
        processed_messages = []
        for msg in result["messages"]:
            if hasattr(msg, 'content'):
                # 处理消息内容，将图像URL转换为简短描述
                processed_content = _process_content_for_storage(getattr(msg, 'content', ""))
                # 创建新的消息对象，使用处理后的内容
                if msg.__class__.__name__ == 'AIMessage':
                    from langchain_core.messages import AIMessage
                    processed_msg = AIMessage(content=processed_content)
                elif msg.__class__.__name__ == 'HumanMessage':
                    from langchain_core.messages import HumanMessage
                    processed_msg = HumanMessage(content=processed_content)
                elif msg.__class__.__name__ == 'SystemMessage':
                    from langchain_core.messages import SystemMessage
                    processed_msg = SystemMessage(content=processed_content)
                else:
                    processed_msg = msg  # 保持其他类型的消息不变
                processed_messages.append(processed_msg)
            else:
                processed_messages.append(msg)
        # 更新结果中的消息
        result['messages'] = processed_messages
    
    # 保存处理后的最终状态到历史记录
    save_history_from_model_state(user_id, result)
    
    # 提取输出内容
    output = ""
    if hasattr(result, 'get'):
        output = result.get("output", "")
        if not output and "messages" in result:
            # 从消息中获取最新AI回复
            messages = result.get("messages", [])
            if messages:
                last_msg = messages[-1]
                if hasattr(last_msg, 'content'):
                    output = last_msg.content
    else:
        output = str(result)
        
    return {"output": output}



# 流式处理版本
def stream_multimodal_agent_executor(user_id: str, query: str, image_url: str, streaming: bool = True) -> Generator[Dict[str, Any], None, None]:
    """
    流式执行多模态智能体 - 用于处理图像输入的流式响应
    
    Args:
        user_id: 用户ID
        query: 查询文本
        image_url: 图像URL
        
    Yields:
        dict: 包含流式处理结果的字典
    """

    logger.critical(f"创建多模态智能体执行器 - 用户ID: {user_id}")
    graph = create_multi_agent_graph(streaming=streaming)
    
    memory = MockMemory(user_id)
    
    
    executor = GraphExecutor(graph, user_id)
    return executor, memory

    # 创建智能体图 - 使用非流式模式，因为我们手动处理流式输出
    # logger.critical(f"创建多模态智能体执行器 - 用户ID: {user_id}, 查询: {query}, 图像URL: {image_url}")
    # graph = create_multi_agent_graph(streaming=True)
    
    # # 加载历史消息
    # history_messages = load_history_for_model_state(user_id)
    
    # # 构建包含图像的多模态消息
    # content_parts = []
    # if query:
    #     content_parts.append({"type": "text", "text": query})
    # if image_url:
    #     content_parts.append({"type": "image_url", "image_url": {"url": image_url}})
    
    # # 创建人类消息，包含文本和图像
    # from langchain_core.messages import HumanMessage
    # human_message = HumanMessage(content=content_parts)
    
    # # 构建初始状态，包含图像信息
    # initial_state = {
    #     "messages": history_messages + [human_message],
    #     "query": query,
    #     "image_url": image_url,
    #     "rag_context": [],
    #     "web_search_context": [],
    #     "image_analysis_summary": "",
    #     "step_count": 0,
    #     "search_count": 0,
    #     "consecutive_search_count": 0,
    #     "output": "",
    #     "next_agent": "router",  # 这将触发路由节点决定使用哪个智能体
    #     "sender": "general_agent"
    # }
    
    # # 流式执行图
    # final_result = None
    # for event in graph.stream(initial_state):
    #     final_result = event  # 保存最后的结果
    #     # 发送中间事件
    #     yield event
    
    # # 在流式处理完成后，处理并保存历史记录
    # if final_result:
    #     # 处理消息内容以避免保存完整的图像URL
    #     from api_gateway.utils.history import _process_content_for_storage
        
    #     if "messages" in final_result:
    #         processed_messages = []
    #         for msg in final_result["messages"]:
    #             if hasattr(msg, 'content'):
    #                 # 处理消息内容，将图像URL转换为简短描述
    #                 processed_content = _process_content_for_storage(getattr(msg, 'content', ""))
    #                 # 创建新的消息对象，使用处理后的内容
    #                 if msg.__class__.__name__ == 'AIMessage':
    #                     from langchain_core.messages import AIMessage
    #                     processed_msg = AIMessage(content=processed_content)
    #                 elif msg.__class__.__name__ == 'HumanMessage':
    #                     from langchain_core.messages import HumanMessage
    #                     processed_msg = HumanMessage(content=processed_content)
    #                 elif msg.__class__.__name__ == 'SystemMessage':
    #                     from langchain_core.messages import SystemMessage
    #                     processed_msg = SystemMessage(content=processed_content)
    #                 else:
    #                     processed_msg = msg  # 保持其他类型的消息不变
    #                 processed_messages.append(processed_msg)
    #             else:
    #                 processed_messages.append(msg)
    #         # 更新结果中的消息
    #         final_result['messages'] = processed_messages
        
    #     # 保存处理后的最终状态到历史记录
    #     save_history_from_model_state(user_id, final_result)
        
    #     # 发送最终输出
    #     output = ""
    #     if hasattr(final_result, 'get'):
    #         output = final_result.get("output", "")
    #         if not output and "messages" in final_result:
    #             # 从消息中获取最新AI回复
    #             messages = final_result.get("messages", [])
    #             if messages:
    #                 last_msg = messages[-1]
    #                 if hasattr(last_msg, 'content'):
    #                     output = last_msg.content
    #     else:
    #         output = str(final_result)
            
    #     yield {"output": output, "final": True}
    
    # executor = GraphExecutor(graph, user_id)

    # memory = MockMemory(user_id)
    return executor, memory

