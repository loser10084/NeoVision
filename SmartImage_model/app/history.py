import json
from typing import Iterable, List, Optional

from redis import Redis
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain.memory import ConversationSummaryBufferMemory

from . import config

redis_client = Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    db=config.REDIS_DB,
    password=config.REDIS_PASSWORD,
    decode_responses=True,
)


def _history_key(user_id: str) -> str:
    return f"{config.CHAT_HISTORY_KEY_PREFIX}{user_id}"


def _summary_key(user_id: str) -> str:
    return f"{config.CHAT_SUMMARY_KEY_PREFIX}{user_id}"


def _normalize_role(role: str) -> str:
    role = (role or "").strip().lower()
    if role in ("ai", "assistant"):
        return "assistant"
    if role in ("human", "user"):
        return "user"
    if role == "system":
        return "system"
    return "user"


class RedisChatMessageHistory(BaseChatMessageHistory):
    def __init__(self, user_id: str):
        self.user_id = user_id

    @property
    def messages(self):
        return load_history_messages(self.user_id)

    def add_message(self, message) -> None:
        self.add_messages([message])

    def add_messages(self, messages) -> None:
        entries = []
        for message in messages or []:
            content = str(getattr(message, "content", "") or "").strip()
            if not content:
                continue
            role = _normalize_role(getattr(message, "type", ""))
            entries.append({"role": role, "content": content})
        append_history_entries(self.user_id, entries)

    def clear(self) -> None:
        redis_client.delete(_history_key(self.user_id))


class InMemoryChatMessageHistory(BaseChatMessageHistory):
    def __init__(self, messages=None):
        self._messages = list(messages or [])

    @property
    def messages(self):
        return list(self._messages)

    def add_message(self, message) -> None:
        self._messages.append(message)

    def add_messages(self, messages) -> None:
        self._messages.extend(messages or [])

    def clear(self) -> None:
        self._messages = []


def append_history_entries(user_id: str, entries: Iterable[dict]) -> None:
    payloads = []
    for entry in entries or []:
        role = _normalize_role(entry.get("role") or "")
        content = str(entry.get("content") or "").strip()
        if not role or not content:
            continue
        payloads.append(json.dumps({"role": role, "content": content}, ensure_ascii=True))

    if not payloads:
        return

    key = _history_key(user_id)
    pipeline = redis_client.pipeline()
    pipeline.rpush(key, *payloads)
    pipeline.expire(key, config.CHAT_HISTORY_TTL_SECONDS)
    pipeline.execute()


def append_exchange(user_id: str, user_content: str, assistant_content: str) -> None:
    entries = []
    if user_content:
        entries.append({"role": "user", "content": user_content})
    if assistant_content:
        entries.append({"role": "assistant", "content": assistant_content})
    append_history_entries(user_id, entries)


def load_history_payloads(user_id: str) -> List[dict]:
    key = _history_key(user_id)
    raw_items = redis_client.lrange(key, 0, -1)
    results: List[dict] = []
    for raw in raw_items:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        role = _normalize_role(data.get("role") or "")
        content = str(data.get("content") or "").strip()
        if not role or not content:
            continue
        results.append({"role": role, "content": content})
    return results


def load_history_messages(user_id: str):
    payloads = load_history_payloads(user_id)
    messages = []
    for item in payloads:
        role = item.get("role")
        content = item.get("content", "")
        if role == "assistant":
            messages.append(AIMessage(content=content))
        elif role == "system":
            messages.append(SystemMessage(content=content))
        else:
            messages.append(HumanMessage(content=content))
    return messages


def load_summary(user_id: str) -> str:
    return redis_client.get(_summary_key(user_id)) or ""


def save_summary(user_id: str, summary: str) -> None:
    summary = (summary or "").strip()
    if not summary:
        return
    key = _summary_key(user_id)
    pipeline = redis_client.pipeline()
    pipeline.set(key, summary)
    pipeline.expire(key, config.CHAT_HISTORY_TTL_SECONDS)
    pipeline.execute()


def build_memory(user_id: str, llm, provided_messages: Optional[List] = None):
    if provided_messages:
        chat_history = InMemoryChatMessageHistory(messages=provided_messages)
        memory = ConversationSummaryBufferMemory(
            llm=llm,
            chat_memory=chat_history,
            memory_key="chat_history",
            return_messages=True,
            max_token_limit=config.CHAT_HISTORY_MAX_TOKENS,
        )
        return memory

    chat_history = RedisChatMessageHistory(user_id)
    memory = ConversationSummaryBufferMemory(
        llm=llm,
        chat_memory=chat_history,
        memory_key="chat_history",
        return_messages=True,
        max_token_limit=config.CHAT_HISTORY_MAX_TOKENS,
    )
    summary = load_summary(user_id)
    if summary:
        memory.moving_summary_buffer = summary
    return memory


def persist_summary(user_id: str, memory) -> None:
    summary = getattr(memory, "moving_summary_buffer", "")
    if summary:
        save_summary(user_id, summary)
