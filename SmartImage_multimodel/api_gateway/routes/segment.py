from io import BytesIO

from flask import Blueprint, jsonify, request, send_file

from segmentation.segmenter import segment_nrrd_bytes, segment_multimodal_nrrd_bytes
from utils import logger

segment_bp = Blueprint("segment", __name__)


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
