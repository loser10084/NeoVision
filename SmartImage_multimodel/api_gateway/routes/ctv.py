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
    file_id = uuid.uuid4().hex
    ext = ext.lstrip(".")
    filename = f"{prefix}.{ext}"
    path = _OUTPUT_DIR / f"{file_id}.{ext}"
    path.write_bytes(content)
    return {
        "fileId": file_id,
        "fileName": filename,
        "downloadUrl": f"/api/ctv/outputs/{file_id}.{ext}",
    }


@ctv_bp.route("/api/ctv/refine", methods=["POST"])
def ctv_refine():
    payloads, filenames, err = _collect_modalities()
    if err is not None:
        if err == "empty":
            return jsonify({"error": "empty file"}), 400
        return jsonify({"error": "missing files (flair, t1, t1c, t2)"}), 400

    try:
        output_bytes = ctv_refine_multimodal_bytes(payloads, filenames=filenames)
    except Exception as exc:
        logger.error(f"[ctv] refine failed: {exc}")
        return jsonify({"error": str(exc)}), 500

    return jsonify(_save_output(output_bytes, "ctv_refined", "nrrd"))


@ctv_bp.route("/api/ctv/expand", methods=["POST"])
def ctv_expand():
    payloads, filenames, err = _collect_modalities()
    if err is not None:
        if err == "empty":
            return jsonify({"error": "empty file"}), 400
        return jsonify({"error": "missing files (flair, t1, t1c, t2)"}), 400

    try:
        output_bytes = ctv_expand_multimodal_bytes(payloads, filenames=filenames)
    except Exception as exc:
        logger.error(f"[ctv] expand failed: {exc}")
        return jsonify({"error": str(exc)}), 500

    return jsonify(_save_output(output_bytes, "ctv_expanded", "nrrd"))


@ctv_bp.route("/api/ctv/heatmap", methods=["POST"])
def ctv_heatmap():
    payloads, filenames, err = _collect_modalities()
    if err is not None:
        if err == "empty":
            return jsonify({"error": "empty file"}), 400
        return jsonify({"error": "missing files (flair, t1, t1c, t2)"}), 400

    try:
        output_bytes = ctv_confidence_multimodal_png(payloads, filenames=filenames)
    except Exception as exc:
        logger.error(f"[ctv] heatmap failed: {exc}")
        return jsonify({"error": str(exc)}), 500

    return jsonify(_save_output(output_bytes, "confidence", "png"))


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
