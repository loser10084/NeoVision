"""
model_agents.llm：
    
"""



from typing import Iterable, List
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
import config
from langchain.callbacks.base import BaseCallbackHandler
from queue import Queue
from utils import logger

# 导出流式回调处理器类
__all__ = ["build_common_llm", "build_image_llm", "build_messages", "build_multimodal_messages", "extract_query", "build_prompt_messages", "format_context", "StreamingCallbackHandler"]

def _normalize_model_name(name: str) -> str:
    if not name:
        return ""
    normalized = name.strip()
    lowered = normalized.lower()
    if lowered.startswith("gpt5"):
        return "gpt-5" + normalized[4:]
    if lowered.startswith("gpt_5"):
        return "gpt-5" + normalized[5:]
    return normalized


class LocalChatOpenAI(ChatOpenAI):
    @property
    def _default_params(self):
        params = super()._default_params
        model_name = (self.model_name or "").lower()
        if model_name.startswith("gpt-5"):
            params.pop("temperature", None)
        return params


def build_common_llm(streaming: bool = False, model_name: str = None, callbacks=None) -> ChatOpenAI:
    """
    创建一个ChatOpenAI实例
    """
    model_name = _normalize_model_name(model_name or config.MODEL_NAME)
    kwargs = {
        "model": model_name,
        "timeout": config.MODEL_TIMEOUT,
        "streaming": streaming,
    }
    
    # 添加回调处理器支持
    if callbacks is not None:
        kwargs["callbacks"] = callbacks
    
    lowered = model_name.lower()
    if not lowered.startswith("gpt-5") and config.MODEL_TEMPERATURE is not None:
        kwargs["temperature"] = config.MODEL_TEMPERATURE
    logger.info(
        f"[llm] model={model_name} temperature={kwargs.get('temperature')} streaming={streaming}"
    )
    return LocalChatOpenAI(**kwargs)

def build_image_llm(streaming: bool = False, model_name: str = None) -> ChatOpenAI:
    """
    创建一个支持图像ChatOpenAI实例，用于图像相关任务
    """
    model_name = _normalize_model_name(model_name or config.IMAGE_MODEL_NAME)
    return build_common_llm(streaming, model_name)


def build_messages(payload) -> List:
    """
    构建消息
    """ 
    messages = []
    if isinstance(payload, list):
        for item in payload:
            role = (item.get("role") or "").lower()
            content = item.get("content", "")
            if role == "system":
                messages.append(SystemMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
            else:
                messages.append(HumanMessage(content=content))
        return messages

    prompt = str(payload or "").strip()
    if prompt:
        messages.append(HumanMessage(content=prompt))
    return messages


def build_multimodal_messages(
    prompt: str, image_url: str, history_messages: List = None, system_prompt: str = None
) -> List:
    """
    构建多模态消息
    """
    messages = [SystemMessage(content=system_prompt or config.SYSTEM_PROMPT)]
    if history_messages:
        messages.extend(history_messages)
    content_parts = []
    if prompt:
        content_parts.append({"type": "text", "text": prompt})
    if image_url:
        content_parts.append({"type": "image_url", "image_url": {"url": image_url}})
    if content_parts:
        messages.append(HumanMessage(content=content_parts))
    return messages


def extract_query(payload) -> str:
    """
    从消息负载中提取查询
    """
    if isinstance(payload, list):
        for item in reversed(payload):
            role = (item.get("role") or "").lower()
            if role in ("user", "human", ""):
                content = item.get("content", "")
                if content:
                    return str(content)
    return str(payload or "").strip()


def build_prompt_messages(payload, context="", history_messages=None):
    """
    构建提示消息
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "{system_prompt}"),
            ("system", "{context}"),
            MessagesPlaceholder("messages"),
        ]
    )
    messages = []
    if history_messages:
        messages.extend(history_messages)
    messages.extend(build_messages(payload))
    return prompt.format_messages(
        system_prompt=config.SYSTEM_PROMPT,
        context=context or "",
        messages=messages,
    )


def format_context(docs: Iterable) -> str:
    """
    格式化文档输出
    """
    if not docs:
        return ""
    lines = ["RAG_CONTEXT:"]
    for i, doc in enumerate(docs, start=1):
        meta = doc.metadata or {}
        source = meta.get("source_uri") or meta.get("file_name") or ""
        header = f"[{i}] {source}" if source else f"[{i}]"
        lines.append(header)
        lines.append(doc.page_content)
    return "\n".join(lines)

class StreamingCallbackHandler(BaseCallbackHandler):
    def __init__(self, token_queue):
        self.token_queue = token_queue

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        if token:
            self.token_queue.put(token)


def build_streaming_callback_handler(queue):
    """构建流式回调处理器"""
    return StreamingCallbackHandler(queue)
    
    return StreamingCallbackHandler(queue)