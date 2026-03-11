from io import BytesIO
from pathlib import Path
import uuid

from flask import Blueprint, jsonify, request, send_file

import config
from segmentation.ctv_runner import ctv_confidence_multimodal_png
from segmentation.segmenter import segment_nrrd_bytes, segment_multimodal_nrrd_bytes
from utils import logger

segment_bp = Blueprint("segment", __name__)
_TEACHING_OUTPUT_DIR = Path(config.BASE_DIR) / "data_storage" / "teaching_outputs"
_TEACHING_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@segment_bp.route("/api/segment/nrrd", methods=["POST"])
def segment_nrrd():
    file = request.files.get("file")
    if file is None:
        return jsonify({"error": "missing file"}), 400

    payload = file.read()
    if not payload:
        return jsonify({"error": "empty file"}), 400

    try:
        output_bytes = segment_nrrd_bytes(payload, filename=file.filename)
    except Exception as exc:
        logger.error(f"[segment] failed: {exc}")
        return jsonify({"error": str(exc)}), 500

    return send_file(
        BytesIO(output_bytes),
        mimetype="application/octet-stream",
        as_attachment=True,
        download_name="label.nrrd",
    )


@segment_bp.route("/api/segment/multimodal", methods=["POST"])
def segment_multimodal():
    files = request.files
    flair = files.get("flair")
    t1 = files.get("t1")
    t1c = files.get("t1c")
    t2 = files.get("t2")
    if not all([flair, t1, t1c, t2]):
        return jsonify({"error": "missing files (flair, t1, t1c, t2)"}), 400

    payloads = {
        "MR_Flair": flair.read(),
        "MR_T1": t1.read(),
        "MR_T1c": t1c.read(),
        "MR_T2": t2.read(),
    }
    if any(not v for v in payloads.values()):
        return jsonify({"error": "empty file"}), 400

    filenames = {
        "MR_Flair": flair.filename,
        "MR_T1": t1.filename,
        "MR_T1c": t1c.filename,
        "MR_T2": t2.filename,
    }

    try:
        output_bytes = segment_multimodal_nrrd_bytes(payloads, filenames=filenames)
    except Exception as exc:
        logger.error(f"[segment] multimodal failed: {exc}")
        return jsonify({"error": str(exc)}), 500

    return send_file(
        BytesIO(output_bytes),
        mimetype="application/octet-stream",
        as_attachment=True,
        download_name="label.nrrd",
    )


@segment_bp.route("/api/segment/teaching/3d", methods=["POST"])
def teaching_segment_3d():
    file = request.files.get("file")
    if file is None:
        return jsonify({"error": "missing file"}), 400

    payload = file.read()
    if not payload:
        return jsonify({"error": "empty file"}), 400

    filename = file.filename or "input.nrrd"
    try:
        label_bytes = segment_nrrd_bytes(payload, filename=filename)
    except Exception as exc:
        logger.error(f"[segment] teaching 3d failed: {exc}")
        return jsonify({"error": str(exc)}), 500

    job_id = uuid.uuid4().hex
    job_dir = _TEACHING_OUTPUT_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    (job_dir / "volume.nrrd").write_bytes(payload)
    (job_dir / "label.nrrd").write_bytes(label_bytes)

    return jsonify(
        {
            "jobId": job_id,
            "volumeUrl": f"/api/segment/teaching/outputs/{job_id}/volume.nrrd",
            "labelUrl": f"/api/segment/teaching/outputs/{job_id}/label.nrrd",
        }
    )


@segment_bp.route("/api/segment/teaching/heatmap", methods=["POST"])
def teaching_heatmap():
    file = request.files.get("file")
    if file is None:
        return jsonify({"error": "missing file"}), 400

    payload = file.read()
    if not payload:
        return jsonify({"error": "empty file"}), 400

    name = file.filename or "input.nrrd"
    stem = Path(name).stem or "input"
    payloads = {
        "MR_Flair": payload,
        "MR_T1": payload,
        "MR_T1c": payload,
        "MR_T2": payload,
    }
    filenames = {
        "MR_Flair": f"{stem}_flair.nrrd",
        "MR_T1": f"{stem}_t1.nrrd",
        "MR_T1c": f"{stem}_t1c.nrrd",
        "MR_T2": f"{stem}_t2.nrrd",
    }

    try:
        png_bytes = ctv_confidence_multimodal_png(payloads, filenames=filenames)
    except Exception as exc:
        logger.error(f"[segment] teaching heatmap failed: {exc}")
        return jsonify({"error": str(exc)}), 500

    job_id = uuid.uuid4().hex
    job_dir = _TEACHING_OUTPUT_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    (job_dir / "heatmap.png").write_bytes(png_bytes)

    return jsonify(
        {
            "jobId": job_id,
            "heatmapUrl": f"/api/segment/teaching/outputs/{job_id}/heatmap.png",
        }
    )


@segment_bp.route("/api/segment/teaching/outputs/<job_id>/<filename>", methods=["GET"])
def teaching_output(job_id: str, filename: str):
    safe_name = Path(filename).name
    if safe_name != filename:
        return jsonify({"error": "invalid filename"}), 400

    target = _TEACHING_OUTPUT_DIR / job_id / safe_name
    if not target.exists() or not target.is_file():
        return jsonify({"error": "not found"}), 404

    suffix = target.suffix.lower()
    mimetype = "application/octet-stream"
    if suffix == ".png":
        mimetype = "image/png"
    elif suffix == ".nrrd":
        mimetype = "application/octet-stream"

    return send_file(
        BytesIO(target.read_bytes()),
        mimetype=mimetype,
        as_attachment=False,
        download_name=target.name,
    )
