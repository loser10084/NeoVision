from time import sleep
import threading
import base64
import time
import hashlib
from queue import Queue

from flask import Blueprint, jsonify, request, Response, stream_with_context
from langchain.callbacks.base import BaseCallbackHandler

from api_gateway.utils import auth
import config
from api_gateway import llm
from api_gateway import history
from api_gateway import agent_runtime
from api_gateway import patient_assistant

from utils import logger

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
    logger.info(f"收到请求: ")
    user_id, error_response, status_code = auth.require_auth(request)
    if error_response:
        return jsonify(error_response), status_code

    payload, image_url = _extract_prompt_and_image(request)
    if image_url:
        logger.debug(f"收到图片请求: {image_url}")
    query = llm.extract_query(payload)

    if not query and not image_url:
        return jsonify({"error": "empty prompt"}), 400

    if query and not image_url:
        shortcut_reply = patient_assistant.handle_patient_assistant_command(
            query=query,
            auth_header=request.headers.get("Authorization", ""),
        )
        if shortcut_reply is not None:
            content = str(shortcut_reply.get("content") or "").strip()
            action = shortcut_reply.get("action")
            if content:
                history.append_exchange(user_id, query, content)
            return jsonify({"content": content, "action": action})

    provided_messages = None
    if isinstance(payload, list):
        provided_messages = llm.build_messages(payload)

    try:

        # 修复图片请求问题 - 历史记录已在build_multimodal_agent_executor内部处理
        if image_url:
            logger.critical(f"收到图片请求: {image_url}")
            result = agent_runtime.build_multimodal_agent_executor(
                user_id=user_id,
                query=query,
                image_url=image_url,
                streaming=True
            )
            output = result.get("output", "")
            # history.append_exchange不再需要调用，因为已在build_multimodal_agent_executor内部处理
            return jsonify({"content": output})

        try:
            executor, memory = agent_runtime.build_agent_executor(
                user_id,
                provided_messages=provided_messages,
                streaming=True,
            )
        except Exception as e:
            logger.error(f"Failed to build agent executor: {str(e)}")
            return
        cached = _get_cached_reply(user_id, query)
        if cached is not None:
            logger.info(f"[agent_cache] hit user={user_id} route=/api/agent/chat")
            return jsonify({"content": cached})
        result = executor.invoke({"input": query, "image_url": image_url})
        output = result.get("output", "") if isinstance(result, dict) else str(result)
    except Exception as exc:
        logger.error(f"Agent call failed: {str(exc)}")
        return jsonify({"error": "agent call failed", "detail": str(exc)}), 500

    if provided_messages is not None:
        history.append_exchange(user_id, query, output)
    else:
        history.persist_summary(user_id, memory)
    _set_cached_reply(user_id, query, output)
    return jsonify({"content": output})


@agent_bp.route("/api/agent/chat/stream", methods=["POST"])
def agent_chat_stream():
    logger.info(f"收到流式请求: ")
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

    def generate():
        # if image_url:
        #     logger.critical(f"收到图片流式请求: {image_url}")
        #     executor, memory = agent_runtime.stream_multimodal_agent_executor(
        #         user_id=user_id,
        #         query=query,
        #         image_url=image_url,
        #         streaming=True
        #     )
        # else:
        #     executor, memory = agent_runtime.build_agent_executor(
        #         user_id,
        #         provided_messages=provided_messages,
        #         streaming=True,
        #     )
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
        output_holder = {"text": "", "error": None}



        def run_agent():


            queue_lock = threading.Lock()
            full_response = []

            def emit(text: str):
                """统一输出通道（线程安全 + 支持换行）"""
                if not text:
                    return
                with queue_lock:
                    full_response.append(text)
                    for ch in text:
                        token_queue.put(ch)

            def handle_tool_calls(msg):
                """处理工具调用（兼容 str / dict / 对象）"""
                tool_calls = getattr(msg, "tool_calls", None)
                if not tool_calls:
                    return

                for call in tool_calls:
                    # 情况 1: 字符串
                    if isinstance(call, str):
                        name, args = call, {}
                    # 情况 2: dict
                    elif isinstance(call, dict):
                        name = call.get("name", "unknown")
                        args = call.get("args", {})
                    # 情况 3: 对象
                    else:
                        name = getattr(call, "name", "unknown")
                        args = getattr(call, "args", {})

                    info = f"\n[正在使用工具: {name} 参数: {args}]\n"
                    # logger.debug(info.strip())
                    if config.SHOW_TOOL_CALLS:
                        emit(info)


            def handle_ai_message(msg):
                """处理AI输出消息"""
                content = getattr(msg, "content", None)
                if content:
                    emit(str(content))
                handle_tool_calls(msg)

            saw_token = False

            def parse_event(event):
                """解析LangGraph事件结构（防止 node_data 是 str）"""
                if not isinstance(event, dict):
                    return

                # 1) 处理 GraphExecutor.stream 的 token 事件
                token = event.get("token")
                if token:
                    nonlocal saw_token
                    saw_token = True
                    emit(str(token))
                    return

                # 2) 处理顶层 output（某些图会直接返回）
                output = event.get("output")
                if output and not saw_token:
                    emit(str(output))

                # 3) 处理顶层 messages（某些图会直接返回）
                top_messages = event.get("messages")
                if isinstance(top_messages, list) and not saw_token:
                    for msg in top_messages:
                        if msg.__class__.__name__ == "AIMessage":
                            handle_ai_message(msg)

                # 4) 处理节点级 messages
                for node_data in event.values():
                    # 必须先判断类型
                    if not isinstance(node_data, dict):
                        continue

                    messages = node_data.get("messages")
                    if not isinstance(messages, list):
                        continue

                    if saw_token:
                        continue
                    for msg in messages:
                        if msg.__class__.__name__ == "AIMessage":
                            handle_ai_message(msg)


            try:
                # 检查executor是否支持流式处理
                if hasattr(executor, 'stream'):
                    try:
                        # 使用LangGraph的流式功能实现流式输出
                        logger.info(f"使用LangGraph流式处理执行查询: {query} image_url: {image_url}")
                        
                        
                        for event in executor.stream(
                            {"input": query, "image_url": image_url}
                        ):
                            parse_event(event)
                                                        


                        final_text = "".join(full_response).strip()
                        if not final_text:
                            # 流式未产出内容时，回退一次常规调用以拿到最终输出
                            result = executor.invoke(
                                {"input": query, "image_url": image_url}
                            )
                            output = result.get("output", "") if isinstance(result, dict) else str(result)
                            if output:
                                emit(str(output))
                            final_text = "".join(full_response).strip() or str(output).strip()
                        output_holder["text"] = final_text
                        
                        # 保存历史记录
                        if output_holder["text"].strip():
                            if provided_messages is not None:
                                history.append_exchange(user_id, query, output_holder["text"].strip())
                            else:
                                # 更新内存中的历史记录并持久化
                                try:
                                    memory.chat_memory.add_user_message(query)
                                    memory.chat_memory.add_ai_message(output_holder["text"].strip())
                                except AttributeError:
                                    # 如果chat_memory不支持add_user_message/add_ai_message方法，使用append_exchange
                                    history.append_exchange(user_id, query, output_holder["text"].strip())
                                history.persist_summary(user_id, memory)
                    
                    except Exception as stream_exc:
                        logger.error(f"LangGraph流式处理失败，回退到常规处理: {str(stream_exc)}", stream_exc)
                        
                        # 检查是否是Redis相关的错误，如果是则跳过流式处理
                        if "Redis" in str(stream_exc) or "RDB" in str(stream_exc) or "snapshot" in str(stream_exc).lower():
                            logger.warning("检测到Redis配置问题，直接使用常规处理")
                            # 直接使用常规处理，避免重复尝试
                            result = executor.invoke({"input": query, "image_url": image_url})
                            output = result.get("output", "") if isinstance(result, dict) else str(result)
                            output_holder["text"] = output
                            if output.strip():
                                if provided_messages is not None:
                                    history.append_exchange(user_id, query, output.strip())
                                else:
                                    history.persist_summary(user_id, memory)
                        else:
                            # 对于其他类型的错误，尝试回退到常规处理
                            try:
                                result = executor.invoke({"input": query, "image_url": image_url})
                                output = result.get("output", "") if isinstance(result, dict) else str(result)
                                output_holder["text"] = output
                                if output.strip():
                                    if provided_messages is not None:
                                        history.append_exchange(user_id, query, output.strip())
                                    else:
                                        history.persist_summary(user_id, memory)
                            except Exception as fallback_exc:
                                logger.error(f"回退处理也失败: {str(fallback_exc)}")
                                raise fallback_exc
                else:
                    # 使用常规处理
                    logger.info(f"使用常规处理执行查询: {query}")
                    result = executor.invoke({"input": query, "image_url": image_url})
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
