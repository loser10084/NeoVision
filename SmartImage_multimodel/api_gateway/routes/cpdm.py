from io import BytesIO

from flask import Blueprint, jsonify, redirect, request, send_file

from segmentation.cpdm_runner import (
    get_cpdm_job,
    get_cpdm_result,
    resolve_cpdm_output,
    submit_cpdm_job,
)
from utils import logger

cpdm_bp = Blueprint("cpdm", __name__)


def _pick_ct_file():
    files = request.files
    return files.get("ct") or files.get("file") or files.get("input")


@cpdm_bp.route("/api/cpdm/ct2pet", methods=["POST"])
def cpdm_ct2pet_submit():
    file = _pick_ct_file()
    if file is None:
        return jsonify({"error": "missing ct file (field: ct)"}), 400

    payload = file.read()
    if not payload:
        return jsonify({"error": "empty ct file"}), 400

    sample_step = request.form.get("sampleStep", type=int)
    device = request.form.get("device", default="", type=str) or None
    patient_id = request.form.get("patientId", type=int)
    study_id = request.form.get("studyId", type=int)
    auth_header = request.headers.get("Authorization", default="", type=str) or ""

    try:
        job = submit_cpdm_job(
            payload,
            filename=file.filename or "ct.npy",
            sample_step=sample_step,
            device=device,
            patient_id=patient_id,
            study_id=study_id,
            auth_header=auth_header,
        )
    except PermissionError as exc:
        logger.error(f"[cpdm] submit unauthorized: {exc}")
        return jsonify({"error": str(exc)}), 401
    except ValueError as exc:
        logger.error(f"[cpdm] submit invalid request: {exc}")
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        logger.error(f"[cpdm] submit failed: {exc}")
        return jsonify({"error": str(exc)}), 500

    job_id = job["jobId"]
    return jsonify(
        {
            **job,
            "statusUrl": f"/api/cpdm/jobs/{job_id}",
            "resultUrl": f"/api/cpdm/jobs/{job_id}/result",
        }
    )


@cpdm_bp.route("/api/cpdm/jobs/<job_id>", methods=["GET"])
def cpdm_job_status(job_id: str):
    job = get_cpdm_job(job_id)
    if job is None:
        return jsonify({"error": "job not found"}), 404
    return jsonify(job)


@cpdm_bp.route("/api/cpdm/jobs/<job_id>/result", methods=["GET"])
def cpdm_job_result(job_id: str):
    job = get_cpdm_job(job_id)
    if job is None:
        return jsonify({"error": "job not found"}), 404
    if job["status"] != "completed":
        return jsonify(job), 409

    result = get_cpdm_result(job_id)
    if result is None:
        return jsonify({"error": "result not ready"}), 409
    return jsonify(result)


@cpdm_bp.route("/api/cpdm/outputs/<job_id>/<filename>", methods=["GET"])
def cpdm_output(job_id: str, filename: str):
    # Only expose PNG download externally.
    if filename != "pet.png":
        return jsonify({"error": "only pet.png is available"}), 404

    target = resolve_cpdm_output(job_id, filename)
    if target is None:
        result = get_cpdm_result(job_id)
        pet_png_url = ""
        if isinstance(result, dict):
            result_obj = result.get("result")
            if isinstance(result_obj, dict):
                pet_png_url = str(result_obj.get("petPngUrl") or "").strip()
        if pet_png_url.startswith("http://") or pet_png_url.startswith("https://"):
            return redirect(pet_png_url, code=302)
        return jsonify({"error": "not found"}), 404

    return send_file(
        BytesIO(target.read_bytes()),
        mimetype="image/png",
        as_attachment=True,
        download_name=target.name,
    )
