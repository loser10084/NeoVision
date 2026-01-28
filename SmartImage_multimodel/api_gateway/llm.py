# api_gateway/llm.py
# LLM模块适配器 - 连接API网关与重构后的模型端

from model_agents.llm import (
    build_common_llm as _build_common_llm,
    build_image_llm as _build_image_llm,
    build_messages as _build_messages,
    build_multimodal_messages as _build_multimodal_messages,
    extract_query as _extract_query,
)
import config


def build_llm(streaming: bool = False, model_name: str = None):
    """
    构建LLM实例 - 与原接口兼容
    """
    return _build_common_llm(streaming=streaming, model_name=model_name)


def build_common_llm(streaming: bool = False, model_name: str = None):
    """
    构建通用LLM实例
    """
    return _build_common_llm(streaming=streaming, model_name=model_name)


def build_image_llm(streaming: bool = False, model_name: str = None):
    """
    构建图像处理LLM实例
    """
    return _build_image_llm(streaming=streaming, model_name=model_name)


def build_messages(payload):
    """
    构建消息 - 与原接口兼容
    """
    return _build_messages(payload)


def build_multimodal_messages(prompt: str, image_url: str, history_messages=None, system_prompt: str = None):
    """
    构建多模态消息 - 与原接口兼容
    """
    return _build_multimodal_messages(
        prompt=prompt,
        image_url=image_url,
        history_messages=history_messages,
        system_prompt=system_prompt or config.IMAGE_SYSTEM_PROMPT
    )


def extract_query(payload) -> str:
    """
    提取查询 - 与原接口兼容
    """
    return _extract_query(payload)