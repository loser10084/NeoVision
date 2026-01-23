from typing import Iterable, List
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from . import config


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


def build_llm(streaming: bool = False, model_name: str = None) -> ChatOpenAI:
    model_name = _normalize_model_name(model_name or config.MODEL_NAME)
    kwargs = {
        "model": model_name,
        "timeout": config.MODEL_TIMEOUT,
        "streaming": streaming,
    }
    lowered = model_name.lower()
    if not lowered.startswith("gpt-5") and config.MODEL_TEMPERATURE is not None:
        kwargs["temperature"] = config.MODEL_TEMPERATURE
    print(
        f"[llm] model={model_name} temperature={kwargs.get('temperature')} streaming={streaming}"
    )
    return LocalChatOpenAI(**kwargs)


def build_messages(payload) -> List:
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
    if isinstance(payload, list):
        for item in reversed(payload):
            role = (item.get("role") or "").lower()
            if role in ("user", "human", ""):
                content = item.get("content", "")
                if content:
                    return str(content)
    return str(payload or "").strip()


def build_prompt_messages(payload, context="", history_messages=None):
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
