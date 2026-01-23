import threading
import base64
import time
import hashlib
from queue import Queue

from flask import Blueprint, jsonify, request, Response, stream_with_context
from langchain.callbacks.base import BaseCallbackHandler

from .. import auth
from .. import config
from .. import llm
from .. import history
from .. import agent_runtime

agent_bp = Blueprint("agent", __name__)

CACHE_TTL_SECONDS = 300
_reply_cache = {}


def _cache_key(user_id: str, query: str) -> str:
    base = f"{user_id}::{query}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def _get_cached_reply(user_id: str, query: str):
    key = _cache_key(user_id, query)
    entry = _reply_cache.get(key)
    if not entry:
        return None
    if time.time() - entry["ts"] > CACHE_TTL_SECONDS:
        _reply_cache.pop(key, None)
        return None
    return entry["text"]


def _set_cached_reply(user_id: str, query: str, text: str):
    if not text:
        return
    _reply_cache[_cache_key(user_id, query)] = {"text": text, "ts": time.time()}


@agent_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True})


@agent_bp.route("/api/agent/history", methods=["GET"])
def agent_history():
    user_id, error_response, status_code = auth.require_auth(request)
    if error_response:
        return jsonify(error_response), status_code
    items = history.load_history_payloads(user_id)
    return jsonify({"messages": items})


def _extract_payload(data):
    return data.get("messages") if "messages" in data else data.get("prompt", "")


def _extract_prompt_and_image(req):
    image_url = None
    prompt = ""
    if req.files:
        file = req.files.get("image") or req.files.get("file")
        if file:
            raw = file.read()
            if raw:
                mime = file.mimetype or "image/png"
                encoded = base64.b64encode(raw).decode("ascii")
                image_url = f"data:{mime};base64,{encoded}"
        prompt = (req.form.get("prompt") or "").strip()
        return prompt, image_url
    data = req.get_json(silent=True) or {}
    payload = _extract_payload(data)
    return payload, None


@agent_bp.route("/api/agent/chat", methods=["POST"])
def agent_chat():
    user_id, error_response, status_code = auth.require_auth(request)
    if error_response:
        return jsonify(error_response), status_code

    payload, image_url = _extract_prompt_and_image(request)
    query = llm.extract_query(payload)

    if not query and not image_url:
        return jsonify({"error": "empty prompt"}), 400

    provided_messages = None
    if isinstance(payload, list):
        provided_messages = llm.build_messages(payload)

    try:
        if image_url:
            chat_llm = llm.build_llm(streaming=False, model_name=config.IMAGE_MODEL_NAME)
            history_messages = history.load_history_messages(user_id)
            messages = llm.build_multimodal_messages(
                query, image_url, history_messages, system_prompt=config.IMAGE_SYSTEM_PROMPT
            )
            result = chat_llm.invoke(messages)
            output = result.content if hasattr(result, "content") else str(result)
            history.append_exchange(user_id, query or "[image]", output)
            return jsonify({"content": output})

        executor, memory = agent_runtime.build_agent_executor(
            user_id,
            provided_messages=provided_messages,
            streaming=False,
        )
        cached = _get_cached_reply(user_id, query)
        if cached is not None:
            print(f"[agent_cache] hit user={user_id} route=/api/agent/chat")
            return jsonify({"content": cached})
        result = executor.invoke({"input": query})
        output = result.get("output", "") if isinstance(result, dict) else str(result)
    except Exception as exc:
        return jsonify({"error": "agent call failed", "detail": str(exc)}), 500

    if provided_messages is not None:
        history.append_exchange(user_id, query, output)
    else:
        history.persist_summary(user_id, memory)
    _set_cached_reply(user_id, query, output)
    return jsonify({"content": output})


@agent_bp.route("/api/agent/chat/stream", methods=["POST"])
def agent_chat_stream():
    user_id, error_response, status_code = auth.require_auth(request)
    if error_response:
        return jsonify(error_response), status_code

    payload, image_url = _extract_prompt_and_image(request)
    query = llm.extract_query(payload)

    if not query and not image_url:
        return jsonify({"error": "empty prompt"}), 400

    provided_messages = None
    if isinstance(payload, list):
        provided_messages = llm.build_messages(payload)

    class _QueueCallbackHandler(BaseCallbackHandler):
        def __init__(self, queue: Queue):
            self.queue = queue

        def on_llm_new_token(self, token: str, **kwargs) -> None:
            if token:
                self.queue.put(token)

    def generate():
        if image_url:
            chat_llm = llm.build_llm(streaming=False, model_name=config.IMAGE_MODEL_NAME)
            history_messages = history.load_history_messages(user_id)
            messages = llm.build_multimodal_messages(
                query, image_url, history_messages, system_prompt=config.IMAGE_SYSTEM_PROMPT
            )
            result = chat_llm.invoke(messages)
            output = result.content if hasattr(result, "content") else str(result)
            history.append_exchange(user_id, query or "[image]", output)
            yield f"data: {output}\n\n"
            yield "data: [DONE]\n\n"
            return

        executor, memory = agent_runtime.build_agent_executor(
            user_id,
            provided_messages=provided_messages,
            streaming=True,
        )
        cached = _get_cached_reply(user_id, query)
        if cached is not None:
            print(f"[agent_cache] hit user={user_id} route=/api/agent/chat/stream")
            yield f"data: {cached}\n\n"
            yield "data: [DONE]\n\n"
            return
        token_queue: Queue = Queue()
        handler = _QueueCallbackHandler(token_queue)
        output_holder = {"text": "", "error": None}

        def run_agent():
            try:
                result = executor.invoke({"input": query}, config={"callbacks": [handler]})
                output = result.get("output", "") if isinstance(result, dict) else str(result)
                output_holder["text"] = output
                if output.strip():
                    if provided_messages is not None:
                        history.append_exchange(user_id, query, output.strip())
                    else:
                        history.persist_summary(user_id, memory)
            except Exception as exc:
                output_holder["error"] = exc
            finally:
                token_queue.put(None)

        thread = threading.Thread(target=run_agent, daemon=True)
        thread.start()

        assistant_content = ""
        while True:
            token = token_queue.get()
            if token is None:
                break
            assistant_content += token
            yield f"data: {token}\n\n"

        if output_holder["error"]:
            yield f"data: [ERROR] {str(output_holder['error'])}\n\n"
            return

        if not assistant_content.strip() and output_holder["text"]:
            yield f"data: {output_holder['text']}\n\n"

        _set_cached_reply(user_id, query, assistant_content.strip() or output_holder["text"])
        yield "data: [DONE]\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream")
