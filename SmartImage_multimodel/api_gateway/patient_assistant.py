from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import requests

import config
from utils import logger


_NAME_PATTERN = r"[\u4e00-\u9fa5A-Za-z0-9\u00b7]{2,24}"
_NAVIGATION_KEYWORDS = (
    "\u8df3\u8f6c",
    "\u8fdb\u5165",
    "\u6253\u5f00",
    "\u524d\u5f80",
    "\u8be6\u60c5\u9875",
    "\u8be6\u60c5\u754c\u9762",
    "\u60a3\u8005\u8be6\u60c5",
)
_QUERY_KEYWORDS = (
    "\u67e5\u8be2",
    "\u68c0\u7d22",
    "\u641c\u7d22",
    "\u67e5\u770b",
    "\u8c03\u53d6",
    "\u83b7\u53d6",
    "\u6570\u636e",
    "\u4fe1\u606f",
    "\u8d44\u6599",
    "\u75c5\u5386",
)
_TOKEN_TRIM_PREFIX = (
    "\u5e2e\u6211\u4eec\u76f4\u63a5\u8df3\u8f6c\u8fdb\u5165",
    "\u5e2e\u6211\u76f4\u63a5\u8df3\u8f6c\u8fdb\u5165",
    "\u5e2e\u6211\u4eec\u8df3\u8f6c\u8fdb\u5165",
    "\u5e2e\u6211\u8df3\u8f6c\u8fdb\u5165",
    "\u5e2e\u6211\u4eec\u76f4\u63a5\u8fdb\u5165",
    "\u5e2e\u6211\u76f4\u63a5\u8fdb\u5165",
    "\u5e2e\u6211\u4eec\u8fdb\u5165",
    "\u5e2e\u6211\u8fdb\u5165",
    "\u5e2e\u6211\u4eec\u76f4\u63a5\u8df3\u8f6c",
    "\u5e2e\u6211\u76f4\u63a5\u8df3\u8f6c",
    "\u67e5\u8be2\u4e00\u4e0b",
    "\u5e2e\u6211\u4eec\u67e5\u8be2\u4e00\u4e0b",
    "\u5e2e\u6211\u67e5\u8be2\u4e00\u4e0b",
    "\u5e2e\u6211\u4eec\u67e5\u8be2",
    "\u5e2e\u6211\u67e5\u8be2",
    "\u5e2e\u6211\u4eec\u67e5\u4e00\u4e0b",
    "\u5e2e\u6211\u67e5\u4e00\u4e0b",
    "\u5e2e\u6211\u4eec\u67e5",
    "\u5e2e\u6211\u67e5",
    "\u67e5\u8be2",
    "\u68c0\u7d22",
    "\u641c\u7d22",
    "\u67e5\u770b",
    "\u8c03\u53d6",
    "\u83b7\u53d6",
    "\u67e5\u4e00\u4e0b",
    "\u67e5\u4e0b",
    "\u8df3\u8f6c\u8fdb\u5165",
    "\u76f4\u63a5\u8df3\u8f6c\u8fdb\u5165",
    "\u8df3\u8f6c",
    "\u76f4\u63a5\u8df3\u8f6c",
    "\u8fdb\u5165",
    "\u76f4\u63a5\u8fdb\u5165",
    "\u6253\u5f00",
    "\u524d\u5f80",
    "\u5e2e\u6211\u4eec",
    "\u5e2e\u6211",
    "\u8bf7",
    "\u9ebb\u70e6",
    "\u76f4\u63a5",
    "\u4e00\u4e0b",
)
_TOKEN_TRIM_SUFFIX = (
    "\u7684\u4e00\u4e9b\u60a3\u8005\u6570\u636e",
    "\u7684\u4e00\u4e9b\u60a3\u8005\u4fe1\u606f",
    "\u7684\u4e00\u4e9b\u60a3\u8005\u8d44\u6599",
    "\u7684\u60a3\u8005\u8be6\u60c5\u754c\u9762",
    "\u7684\u60a3\u8005\u8be6\u60c5\u9875",
    "\u7684\u60a3\u8005\u8be6\u60c5",
    "\u60a3\u8005\u8be6\u60c5\u754c\u9762",
    "\u60a3\u8005\u8be6\u60c5\u9875",
    "\u60a3\u8005\u8be6\u60c5",
    "\u60a3\u8005\u6570\u636e",
    "\u60a3\u8005\u4fe1\u606f",
    "\u60a3\u8005\u8d44\u6599",
    "\u60a3\u8005\u75c5\u5386",
    "\u60a3\u8005",
    "\u8be6\u60c5\u754c\u9762",
    "\u8be6\u60c5\u9875",
    "\u8be6\u60c5",
    "\u6570\u636e",
    "\u4fe1\u606f",
    "\u8d44\u6599",
    "\u75c5\u5386",
    "\u9875\u9762",
    "\u754c\u9762",
)
_INVALID_NAMES = {
    "\u60a3\u8005",
    "\u8be6\u60c5",
    "\u8be6\u60c5\u9875",
    "\u8be6\u60c5\u754c\u9762",
    "\u9875\u9762",
    "\u754c\u9762",
    "\u6570\u636e",
    "\u4fe1\u606f",
    "\u8d44\u6599",
    "\u75c5\u5386",
}


@dataclass
class PatientIntent:
    intent: str
    keyword: str


def handle_patient_assistant_command(query: str, auth_header: str | None = None) -> dict[str, Any] | None:
    intent = _parse_intent(query)
    if intent is None:
        return None

    try:
        candidates = _search_patients(intent.keyword, auth_header=auth_header)
    except Exception as exc:
        logger.error(f"[patient_assistant] search failed: {exc}")
        return {
            "content": "\u60a3\u8005\u68c0\u7d22\u6682\u65f6\u4e0d\u53ef\u7528\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5\u3002",
            "action": None,
        }

    if not candidates:
        return {
            "content": f"\u672a\u68c0\u7d22\u5230\u201c{intent.keyword}\u201d\u76f8\u5173\u60a3\u8005\uff0c\u8bf7\u786e\u8ba4\u59d3\u540d\u6216\u75c5\u5386\u53f7\u540e\u91cd\u8bd5\u3002",
            "action": None,
        }

    primary = _select_primary_candidate(intent.keyword, candidates)
    if not primary:
        return {
            "content": "\u68c0\u7d22\u5230\u5019\u9009\u60a3\u8005\uff0c\u4f46\u672a\u80fd\u5b9a\u4f4d\u53ef\u7528\u8bb0\u5f55\uff0c\u8bf7\u6362\u4e00\u4e2a\u5173\u952e\u8bcd\u91cd\u8bd5\u3002",
            "action": None,
        }

    if intent.intent == "navigate":
        return _build_navigation_reply(intent, candidates, primary)

    return _build_query_reply(intent, candidates, primary, auth_header=auth_header)


def _parse_intent(query: str) -> PatientIntent | None:
    text = _normalize_text(query)
    if not text:
        return None

    has_navigation = any(key in text for key in _NAVIGATION_KEYWORDS)
    has_query = any(key in text for key in _QUERY_KEYWORDS)
    if not has_navigation and not has_query:
        return None

    name = _extract_name(text)
    if not name:
        return None

    return PatientIntent(intent="navigate" if has_navigation else "query", keyword=name)


def _normalize_text(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    text = re.sub(r"[\u3002\uff0c\uff1f\uff01\uff1b\uff1a,.!?;:\"'`“”‘’（）()\[\]{}]", " ", text)
    text = re.sub(r"\s+", "", text)
    return text


def _extract_name(text: str) -> str:
    patterns = [
        rf"(?:\u67e5\u8be2|\u68c0\u7d22|\u641c\u7d22|\u67e5\u770b|\u8c03\u53d6|\u83b7\u53d6|\u67e5\u4e00\u4e0b|\u67e5\u4e0b)(?P<name>{_NAME_PATTERN})",
        rf"(?:\u8df3\u8f6c|\u8fdb\u5165|\u6253\u5f00|\u524d\u5f80)(?P<name>{_NAME_PATTERN})",
        rf"(?P<name>{_NAME_PATTERN})\u7684(?:\u4e00\u4e9b|\u8fd9\u4f4d|\u8be5)?\u60a3\u8005",
        rf"(?P<name>{_NAME_PATTERN})(?:\u60a3\u8005)?(?:\u8be6\u60c5|\u8be6\u60c5\u9875|\u8be6\u60c5\u754c\u9762)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        name = _clean_name(match.group("name"))
        if _is_valid_name(name):
            return name

    tokens = re.findall(_NAME_PATTERN, text)
    for token in tokens:
        name = _clean_name(token)
        if _is_valid_name(name):
            return name
    return ""


def _clean_name(raw: str) -> str:
    name = str(raw or "").strip()
    for prefix in _TOKEN_TRIM_PREFIX:
        if name.startswith(prefix):
            name = name[len(prefix):]
    for suffix in _TOKEN_TRIM_SUFFIX:
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    name = name.strip("\u7684 ")
    return name


def _is_valid_name(name: str) -> bool:
    if not name:
        return False
    if name in _INVALID_NAMES:
        return False
    return len(name) >= 2


def _build_navigation_reply(intent: PatientIntent, candidates: list[dict[str, Any]], primary: dict[str, Any]) -> dict[str, Any]:
    exact_matches = _find_exact_matches(intent.keyword, candidates)
    if len(exact_matches) == 1:
        target = exact_matches[0]
        target_id = _safe_int(target.get("id"))
        if target_id:
            return {
                "content": f"\u5df2\u5b9a\u4f4d\u5230\u60a3\u8005\u300c{target.get('name') or intent.keyword}\u300d\uff0c\u6b63\u5728\u6253\u5f00\u60a3\u8005\u8be6\u60c5\u9875\u3002",
                "action": {
                    "type": "open_patient_detail",
                    "patientId": target_id,
                    "patientName": str(target.get("name") or intent.keyword),
                },
            }

    if len(candidates) > 1:
        return {
            "content": f"\u68c0\u7d22\u5230 {len(candidates)} \u4f4d\u76f8\u5173\u60a3\u8005\uff0c\u6211\u5df2\u5e2e\u4f60\u6253\u5f00\u60a3\u8005\u5217\u8868\u5e76\u81ea\u52a8\u7b5b\u9009\u201c{intent.keyword}\u201d\u3002",
            "action": {
                "type": "open_patient_list",
                "keyword": intent.keyword,
            },
        }

    target_id = _safe_int(primary.get("id"))
    if target_id:
        return {
            "content": f"\u5df2\u5b9a\u4f4d\u5230\u60a3\u8005\u300c{primary.get('name') or intent.keyword}\u300d\uff0c\u6b63\u5728\u6253\u5f00\u60a3\u8005\u8be6\u60c5\u9875\u3002",
            "action": {
                "type": "open_patient_detail",
                "patientId": target_id,
                "patientName": str(primary.get("name") or intent.keyword),
            },
        }

    return {
        "content": "\u5df2\u5339\u914d\u5230\u60a3\u8005\uff0c\u4f46\u672a\u83b7\u5f97\u53ef\u8df3\u8f6c\u7684\u60a3\u8005ID\uff0c\u8bf7\u624b\u52a8\u4ece\u60a3\u8005\u5217\u8868\u8fdb\u5165\u3002",
        "action": {
            "type": "open_patient_list",
            "keyword": intent.keyword,
        },
    }


def _build_query_reply(
    intent: PatientIntent,
    candidates: list[dict[str, Any]],
    primary: dict[str, Any],
    auth_header: str | None = None,
) -> dict[str, Any]:
    detail = None
    patient_id = _safe_int(primary.get("id"))
    if patient_id:
        try:
            detail = _get_patient_detail(patient_id, auth_header=auth_header)
        except Exception as exc:
            logger.warning(f"[patient_assistant] detail query failed: {exc}")

    patient = detail if isinstance(detail, dict) else primary
    name = str(patient.get("name") or intent.keyword)
    lines = [
        f"\u5df2\u68c0\u7d22\u5230\u60a3\u8005\u300c{name}\u300d\uff1a",
        f"- \u60a3\u8005ID\uff1a{patient.get('id') or '-'}",
        f"- \u6027\u522b/\u5e74\u9f84\uff1a{patient.get('sex') or '-'} / {patient.get('age') or '-'}",
        f"- \u8bca\u65ad\uff1a{patient.get('diagnosis') or '-'}",
        f"- \u5206\u671f\uff1a{patient.get('stage') or '-'}",
        f"- \u72b6\u6001\uff1a{patient.get('status') or '-'}",
        f"- \u6700\u8fd1\u66f4\u65b0\uff1a{patient.get('lastUpdate') or '-'}",
    ]
    if len(candidates) > 1:
        lines.append(f"\u540c\u65f6\u68c0\u7d22\u5230 {len(candidates)} \u4f4d\u76f8\u5173\u60a3\u8005\u3002")
    lines.append(f"\u5982\u9700\u6211\u76f4\u63a5\u6253\u5f00\u8be6\u60c5\u9875\uff0c\u8bf7\u8bf4\u201c\u8fdb\u5165{name}\u7684\u60a3\u8005\u8be6\u60c5\u201d\u3002")
    return {"content": "\n".join(lines), "action": None}


def _find_exact_matches(keyword: str, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    target = _name_key(keyword)
    if not target:
        return []
    matches: list[dict[str, Any]] = []
    for item in candidates:
        current = _name_key(item.get("name"))
        if current and current == target:
            matches.append(item)
    return matches


def _select_primary_candidate(keyword: str, candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    exact = _find_exact_matches(keyword, candidates)
    if exact:
        return exact[0]
    number = _safe_int(keyword)
    if number is not None:
        for item in candidates:
            if _safe_int(item.get("id")) == number:
                return item
    return candidates[0] if candidates else None


def _name_key(value: Any) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return ""
    return re.sub(r"\s+", "", text)


def _search_patients(keyword: str, auth_header: str | None = None) -> list[dict[str, Any]]:
    payload = _request_backend_json(
        path="/api/patients",
        params={"keyword": keyword},
        auth_header=auth_header,
    )
    if not isinstance(payload, list):
        return []
    return [item for item in payload if isinstance(item, dict)]


def _get_patient_detail(patient_id: int, auth_header: str | None = None) -> dict[str, Any] | None:
    payload = _request_backend_json(
        path=f"/api/patients/{int(patient_id)}",
        params=None,
        auth_header=auth_header,
    )
    if not isinstance(payload, dict):
        return None
    return payload


def _request_backend_json(path: str, params: dict[str, Any] | None, auth_header: str | None) -> Any:
    base_url = _normalize_base_url(getattr(config, "BACKEND_API_BASE_URL", "http://127.0.0.1:8080"))
    url = f"{base_url}{path}"
    headers = _build_headers(auth_header)
    timeout = max(5, min(int(getattr(config, "BACKEND_UPLOAD_TIMEOUT_SECONDS", 120) or 120), 30))

    response = requests.get(url, params=params or None, headers=headers, timeout=timeout)
    payload = _parse_json(response)
    if response.status_code == 401:
        raise PermissionError("patient assistant unauthorized")
    if response.status_code < 200 or response.status_code >= 300:
        raise RuntimeError(f"patient assistant backend failed: HTTP {response.status_code}")
    if isinstance(payload, dict) and "code" in payload:
        if payload.get("code") != 0:
            raise RuntimeError(str(payload.get("message") or "patient assistant backend error"))
        return payload.get("data")
    return payload


def _parse_json(response: requests.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return None


def _normalize_base_url(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return "http://127.0.0.1:8080"
    return text[:-1] if text.endswith("/") else text


def _build_headers(auth_header: str | None) -> dict[str, str]:
    header_value = str(auth_header or "").strip()
    if not header_value:
        token = str(getattr(config, "BACKEND_SERVICE_BEARER_TOKEN", "") or "").strip()
        if token:
            header_value = token if token.lower().startswith("bearer ") else f"Bearer {token}"
    if not header_value:
        return {}
    return {"Authorization": header_value}


def _safe_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None
