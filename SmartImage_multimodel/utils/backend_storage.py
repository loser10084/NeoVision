from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

import config
from utils import logger


_BACKEND_STORAGE_MODES = {"oss", "backend", "backend_oss"}


@dataclass
class BackendUploadResult:
    file_id: int | None
    file_path: str
    file_type: str
    object_name: str | None = None


def use_backend_storage() -> bool:
    mode = str(getattr(config, "MODEL_OUTPUT_STORAGE", "oss") or "oss").strip().lower()
    return mode in _BACKEND_STORAGE_MODES


def ensure_storage_context(patient_id: int | None, study_id: int | None) -> None:
    if not use_backend_storage():
        return
    if not patient_id or not study_id:
        raise ValueError("missing patientId/studyId for OSS storage")


def upload_output_bytes(
    *,
    patient_id: int,
    study_id: int,
    filename: str,
    file_type: str,
    content: bytes,
    auth_header: str | None = None,
) -> BackendUploadResult:
    if not patient_id or not study_id:
        raise ValueError("patientId/studyId is required")
    if not content:
        raise ValueError("empty file content")

    base_url = _normalize_base_url(getattr(config, "BACKEND_API_BASE_URL", "http://127.0.0.1:8080"))
    url = f"{base_url}/api/patients/{int(patient_id)}/studies/{int(study_id)}/upload"

    headers = _build_headers(auth_header)
    files = {
        "file": (
            filename or "output.bin",
            content,
            "application/octet-stream",
        )
    }
    data = {"fileType": file_type or "bin"}

    timeout_seconds = int(getattr(config, "BACKEND_UPLOAD_TIMEOUT_SECONDS", 120) or 120)
    try:
        response = requests.post(url, headers=headers, data=data, files=files, timeout=timeout_seconds)
    except requests.RequestException as exc:
        raise RuntimeError(f"backend upload request failed: {exc}") from exc

    payload = _parse_json(response)
    if response.status_code == 401:
        raise PermissionError("backend upload unauthorized (token missing or expired)")
    if response.status_code < 200 or response.status_code >= 300:
        message = _pick_message(payload) or f"HTTP {response.status_code}"
        raise RuntimeError(f"backend upload failed: {message}")

    if not isinstance(payload, dict):
        raise RuntimeError("backend upload failed: invalid response body")
    if payload.get("code") != 0:
        message = _pick_message(payload) or "unknown error"
        raise RuntimeError(f"backend upload failed: {message}")

    data_obj = payload.get("data")
    if not isinstance(data_obj, dict):
        raise RuntimeError("backend upload failed: missing data field")

    file_path = str(data_obj.get("filePath") or "").strip()
    if not file_path:
        raise RuntimeError("backend upload failed: missing filePath in response")

    result = BackendUploadResult(
        file_id=_to_int_or_none(data_obj.get("fileId")),
        file_path=file_path,
        file_type=str(data_obj.get("fileType") or file_type or "").strip(),
        object_name=str(data_obj.get("objectName") or "").strip() or None,
    )
    logger.info(
        f"[storage] uploaded via backend: patient={patient_id}, study={study_id}, "
        f"type={result.file_type}, url={result.file_path}"
    )
    return result


def _normalize_base_url(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return "http://127.0.0.1:8080"
    return text[:-1] if text.endswith("/") else text


def _build_headers(auth_header: str | None) -> dict[str, str]:
    header_value = (auth_header or "").strip()
    if not header_value:
        service_token = str(getattr(config, "BACKEND_SERVICE_BEARER_TOKEN", "") or "").strip()
        if service_token:
            if service_token.lower().startswith("bearer "):
                header_value = service_token
            else:
                header_value = f"Bearer {service_token}"
    if not header_value:
        return {}
    return {"Authorization": header_value}


def _parse_json(response: requests.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return None


def _pick_message(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    for key in ("message", "error", "msg"):
        value = payload.get(key)
        if value:
            return str(value)
    data = payload.get("data")
    if isinstance(data, dict):
        for key in ("message", "error", "msg"):
            value = data.get(key)
            if value:
                return str(value)
    return ""


def _to_int_or_none(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None
