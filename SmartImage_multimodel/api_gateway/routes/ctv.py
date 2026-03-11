from io import BytesIO
from pathlib import Path
import uuid

from flask import Blueprint, jsonify, request, send_file

from segmentation.ctv_runner import (
    ctv_expand_multimodal_bytes,
    ctv_refine_multimodal_bytes,
    ctv_confidence_multimodal_png,
)
from utils import logger
from utils.backend_storage import ensure_storage_context, upload_output_bytes, use_backend_storage
import config

ctv_bp = Blueprint("ctv", __name__)

_OUTPUT_DIR = Path(config.BASE_DIR) / "data_storage" / "ctv_outputs"
_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _get_file(files, *names):
    for name in names:
        f = files.get(name)
        if f is not None:
            return f
    return None


def _collect_modalities():
    files = request.files
    flair = _get_file(files, "flair", "MR_Flair")
    t1 = _get_file(files, "t1", "MR_T1")
    t1c = _get_file(files, "t1c", "MR_T1c")
    t2 = _get_file(files, "t2", "MR_T2")
    if not all([flair, t1, t1c, t2]):
        return None, None, (flair, t1, t1c, t2)

    payloads = {
        "MR_Flair": flair.read(),
        "MR_T1": t1.read(),
        "MR_T1c": t1c.read(),
        "MR_T2": t2.read(),
    }
    if any(not v for v in payloads.values()):
        return None, None, "empty"

    filenames = {
        "MR_Flair": flair.filename,
        "MR_T1": t1.filename,
        "MR_T1c": t1c.filename,
        "MR_T2": t2.filename,
    }
    return payloads, filenames, None


def _save_output(content: bytes, prefix: str, ext: str) -> dict:
    return _save_output_with_context(
        content,
        prefix=prefix,
        ext=ext,
        file_type=f"{prefix}.{ext.lstrip('.')}",
        patient_id=None,
        study_id=None,
        auth_header="",
    )


def _save_output_with_context(
    content: bytes,
    *,
    prefix: str,
    ext: str,
    file_type: str,
    patient_id: int | None,
    study_id: int | None,
    auth_header: str,
) -> dict:
    file_id = uuid.uuid4().hex
    ext = ext.lstrip(".")
    filename = f"{prefix}.{ext}"

    if use_backend_storage():
        ensure_storage_context(patient_id, study_id)
        uploaded = upload_output_bytes(
            patient_id=int(patient_id),
            study_id=int(study_id),
            filename=filename,
            file_type=file_type,
            content=content,
            auth_header=auth_header,
        )
        return {
            "fileId": uploaded.file_id or file_id,
            "fileName": filename,
            "downloadUrl": uploaded.file_path,
            "storage": "oss",
        }

    path = _OUTPUT_DIR / f"{file_id}.{ext}"
    path.write_bytes(content)
    return {
        "fileId": file_id,
        "fileName": filename,
        "downloadUrl": f"/api/ctv/outputs/{file_id}.{ext}",
        "storage": "local",
    }


def _parse_storage_context() -> tuple[int | None, int | None, str]:
    patient_id = request.form.get("patientId", type=int)
    study_id = request.form.get("studyId", type=int)
    auth_header = request.headers.get("Authorization", default="", type=str) or ""
    return patient_id, study_id, auth_header


@ctv_bp.route("/api/ctv/refine", methods=["POST"])
def ctv_refine():
    patient_id, study_id, auth_header = _parse_storage_context()
    payloads, filenames, err = _collect_modalities()
    if err is not None:
        if err == "empty":
            return jsonify({"error": "empty file"}), 400
        return jsonify({"error": "missing files (flair, t1, t1c, t2)"}), 400

    try:
        ensure_storage_context(patient_id, study_id)
        output_bytes = ctv_refine_multimodal_bytes(payloads, filenames=filenames)
        result = _save_output_with_context(
            output_bytes,
            prefix="ctv_refined",
            ext="nrrd",
            file_type="ctv.refined.nrrd",
            patient_id=patient_id,
            study_id=study_id,
            auth_header=auth_header,
        )
    except PermissionError as exc:
        logger.error(f"[ctv] refine upload unauthorized: {exc}")
        return jsonify({"error": str(exc)}), 401
    except ValueError as exc:
        logger.error(f"[ctv] refine invalid request: {exc}")
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        logger.error(f"[ctv] refine failed: {exc}")
        return jsonify({"error": str(exc)}), 500

    return jsonify(result)


@ctv_bp.route("/api/ctv/expand", methods=["POST"])
def ctv_expand():
    patient_id, study_id, auth_header = _parse_storage_context()
    payloads, filenames, err = _collect_modalities()
    if err is not None:
        if err == "empty":
            return jsonify({"error": "empty file"}), 400
        return jsonify({"error": "missing files (flair, t1, t1c, t2)"}), 400

    try:
        ensure_storage_context(patient_id, study_id)
        output_bytes = ctv_expand_multimodal_bytes(payloads, filenames=filenames)
        result = _save_output_with_context(
            output_bytes,
            prefix="ctv_expanded",
            ext="nrrd",
            file_type="ctv.expanded.nrrd",
            patient_id=patient_id,
            study_id=study_id,
            auth_header=auth_header,
        )
    except PermissionError as exc:
        logger.error(f"[ctv] expand upload unauthorized: {exc}")
        return jsonify({"error": str(exc)}), 401
    except ValueError as exc:
        logger.error(f"[ctv] expand invalid request: {exc}")
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        logger.error(f"[ctv] expand failed: {exc}")
        return jsonify({"error": str(exc)}), 500

    return jsonify(result)


@ctv_bp.route("/api/ctv/heatmap", methods=["POST"])
def ctv_heatmap():
    patient_id, study_id, auth_header = _parse_storage_context()
    payloads, filenames, err = _collect_modalities()
    if err is not None:
        if err == "empty":
            return jsonify({"error": "empty file"}), 400
        return jsonify({"error": "missing files (flair, t1, t1c, t2)"}), 400

    try:
        ensure_storage_context(patient_id, study_id)
        output_bytes = ctv_confidence_multimodal_png(payloads, filenames=filenames)
        result = _save_output_with_context(
            output_bytes,
            prefix="confidence",
            ext="png",
            file_type="ctv.heatmap.png",
            patient_id=patient_id,
            study_id=study_id,
            auth_header=auth_header,
        )
    except PermissionError as exc:
        logger.error(f"[ctv] heatmap upload unauthorized: {exc}")
        return jsonify({"error": str(exc)}), 401
    except ValueError as exc:
        logger.error(f"[ctv] heatmap invalid request: {exc}")
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        logger.error(f"[ctv] heatmap failed: {exc}")
        return jsonify({"error": str(exc)}), 500

    return jsonify(result)


@ctv_bp.route("/api/ctv/outputs/<file_id>", methods=["GET"])
def ctv_output(file_id: str):
    target = _OUTPUT_DIR / file_id
    if target.suffix:
        path = target
    else:
        for ext in ("nrrd", "png"):
            cand = _OUTPUT_DIR / f"{file_id}.{ext}"
            if cand.exists():
                path = cand
                break
        else:
            path = target
    if not path.exists():
        return jsonify({"error": "not found"}), 404
    mimetype = "application/octet-stream"
    if path.suffix.lower() == ".png":
        mimetype = "image/png"
    return send_file(
        BytesIO(path.read_bytes()),
        mimetype=mimetype,
        as_attachment=True,
        download_name=path.name,
    )
