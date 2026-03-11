from __future__ import annotations

import json
from io import BytesIO
import os
import shutil
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from PIL import Image

import config
from utils.backend_storage import ensure_storage_context, upload_output_bytes, use_backend_storage
from utils import logger

_CPDM_OUTPUT_ROOT = Path(config.BASE_DIR) / "data_storage" / "cpdm_outputs"
_CPDM_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

_CPDM_JOB_WORK_ROOT = _CPDM_OUTPUT_ROOT / "_jobs"
_CPDM_JOB_WORK_ROOT.mkdir(parents=True, exist_ok=True)

_INPUT_SAMPLE_NAME = "000000"


@dataclass
class CPDMJob:
    job_id: str
    sample_step: int
    patient_id: int | None = None
    study_id: int | None = None
    status: str = "queued"
    progress: int = 0
    message: str = "queued"
    error: str | None = None
    output: dict[str, Any] | None = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


@dataclass
class CPDMRuntime:
    root_dir: Path
    python_exe: str
    template_config: Path
    model_ckpt: Path
    vqgan_ckpt: Path
    unet_ckpt: Path
    sample_step: int
    gpu_ids: str
    timeout_seconds: int
    mplconfigdir: Path


_jobs: dict[str, CPDMJob] = {}
_jobs_lock = threading.Lock()
_cpdm_root_cache: Path | None = None
_warned_invalid_mplconfig = False


def submit_cpdm_job(
    ct_payload: bytes,
    filename: str,
    *,
    sample_step: int | None = None,
    device: str | None = None,
    patient_id: int | None = None,
    study_id: int | None = None,
    auth_header: str | None = None,
) -> dict[str, Any]:
    if not ct_payload:
        raise ValueError("empty file")

    backend_mode = use_backend_storage()
    storage_via_backend = backend_mode and bool(patient_id) and bool(study_id)
    if storage_via_backend:
        ensure_storage_context(patient_id, study_id)
    elif backend_mode:
        logger.warning("[cpdm] missing patientId/studyId, fallback to local output storage")

    runtime = _resolve_runtime(sample_step=sample_step, device=device)

    job_id = uuid.uuid4().hex
    job = CPDMJob(
        job_id=job_id,
        sample_step=runtime.sample_step,
        patient_id=patient_id,
        study_id=study_id,
        status="queued",
        progress=0,
        message="queued",
    )
    with _jobs_lock:
        _jobs[job_id] = job

    thread = threading.Thread(
        target=_run_cpdm_job,
        args=(job_id, ct_payload, filename, runtime, patient_id, study_id, (auth_header or "").strip()),
        daemon=True,
        name=f"cpdm-job-{job_id}",
    )
    thread.start()

    return _serialize_job(job)


def get_cpdm_job(job_id: str) -> dict[str, Any] | None:
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is not None:
            return _serialize_job(job)
    return _load_cpdm_job_from_disk(job_id)


def get_cpdm_result(job_id: str) -> dict[str, Any] | None:
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is not None and job.status == "completed" and isinstance(job.output, dict):
            return {
                "jobId": job.job_id,
                "status": job.status,
                "result": dict(job.output),
            }

    disk_job = _load_cpdm_job_from_disk(job_id)
    if disk_job and disk_job.get("status") == "completed" and isinstance(disk_job.get("result"), dict):
        return {
            "jobId": str(disk_job.get("jobId", job_id)),
            "status": "completed",
            "result": dict(disk_job["result"]),
        }
    return None


def _load_cpdm_job_from_disk(job_id: str) -> dict[str, Any] | None:
    job_dir = _CPDM_OUTPUT_ROOT / job_id
    if not job_dir.is_dir():
        return None

    created_at = job_dir.stat().st_ctime
    updated_at = job_dir.stat().st_mtime
    sample_step = int(config.CPDM_SAMPLE_STEP)
    result_payload: dict[str, Any] | None = None

    meta_path = job_dir / "meta.json"
    if meta_path.is_file():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            created_at = float(meta.get("createdAt", created_at))
            sample_step = int(meta.get("sampleStep", sample_step))
            result_obj = meta.get("result")
            if isinstance(result_obj, dict):
                result_payload = dict(result_obj)
        except Exception as exc:
            logger.warning(f"[cpdm] failed to parse meta for job={job_id}: {exc}")

    if result_payload:
        return {
            "jobId": job_id,
            "status": "completed",
            "progress": 100,
            "message": "completed",
            "createdAt": created_at,
            "updatedAt": updated_at,
            "sampleStep": sample_step,
            "result": result_payload,
        }

    pet_png = job_dir / "pet.png"
    if pet_png.is_file():
        return {
            "jobId": job_id,
            "status": "completed",
            "progress": 100,
            "message": "completed",
            "createdAt": created_at,
            "updatedAt": updated_at,
            "sampleStep": sample_step,
            "result": {
                "petPngUrl": f"/api/cpdm/outputs/{job_id}/pet.png",
                "sampleStep": sample_step,
            },
        }

    return {
        "jobId": job_id,
        "status": "failed",
        "progress": 100,
        "message": "job state lost after restart",
        "error": "job not found in memory and result is missing",
        "createdAt": created_at,
        "updatedAt": updated_at,
        "sampleStep": sample_step,
    }


def resolve_cpdm_output(job_id: str, filename: str) -> Path | None:
    safe_name = Path(filename).name
    if safe_name != filename:
        return None
    target = _CPDM_OUTPUT_ROOT / job_id / safe_name
    if not target.exists() or not target.is_file():
        return None
    return target


def _serialize_job(job: CPDMJob) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "jobId": job.job_id,
        "status": job.status,
        "progress": int(job.progress),
        "message": job.message,
        "createdAt": job.created_at,
        "updatedAt": job.updated_at,
        "sampleStep": job.sample_step,
    }
    if job.patient_id:
        payload["patientId"] = int(job.patient_id)
    if job.study_id:
        payload["studyId"] = int(job.study_id)
    if job.error:
        payload["error"] = job.error
    if job.output:
        payload["result"] = job.output
    return payload


def _set_job(job_id: str, **kwargs: Any) -> None:
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is None:
            return
        for key, value in kwargs.items():
            setattr(job, key, value)
        job.updated_at = time.time()


def _resolve_runtime(sample_step: int | None, device: str | None) -> CPDMRuntime:
    root_dir = _resolve_cpdm_root_dir()
    template_config = _resolve_template_config(root_dir)
    model_ckpt = _resolve_weight_file(
        raw_path=config.CPDM_MODEL_CKPT,
        root_dir=root_dir,
        fallback_names=("CPDM_latest_model_200.pth",),
        title="CPDM_MODEL_CKPT",
    )
    vqgan_ckpt = _resolve_weight_file(
        raw_path=config.CPDM_VQGAN_CKPT,
        root_dir=root_dir,
        fallback_names=("VQGAN_1_3_69.ckpt",),
        title="CPDM_VQGAN_CKPT",
    )
    unet_ckpt = _resolve_weight_file(
        raw_path=config.CPDM_UNET_CKPT,
        root_dir=root_dir,
        fallback_names=("UNET_AttentionMap_step_9000.ckpt",),
        title="CPDM_UNET_CKPT",
    )

    python_exe = _resolve_python_exe()

    if sample_step is None:
        step = int(config.CPDM_SAMPLE_STEP)
    else:
        step = int(sample_step)
    if step <= 1:
        raise ValueError("sampleStep must be > 1")

    gpu_ids = (config.CPDM_GPU_IDS or "-1").strip() or "-1"
    if device:
        dev = device.lower().strip()
        if dev == "cpu":
            gpu_ids = "-1"

    mplconfigdir = _resolve_mplconfig_dir(root_dir)

    runtime = CPDMRuntime(
        root_dir=root_dir,
        python_exe=python_exe,
        template_config=template_config,
        model_ckpt=model_ckpt,
        vqgan_ckpt=vqgan_ckpt,
        unet_ckpt=unet_ckpt,
        sample_step=step,
        gpu_ids=gpu_ids,
        timeout_seconds=int(config.CPDM_TIMEOUT_SECONDS),
        mplconfigdir=mplconfigdir,
    )

    missing = [
        path
        for path in (
            runtime.root_dir,
            runtime.template_config,
            runtime.model_ckpt,
            runtime.vqgan_ckpt,
            runtime.unet_ckpt,
        )
        if not path.exists()
    ]
    if missing:
        missing_text = ", ".join(str(path) for path in missing)
        raise FileNotFoundError(f"CPDM path not found: {missing_text}")

    logger.info(
        "[cpdm] runtime resolved: "
        f"root={runtime.root_dir}, template={runtime.template_config}, "
        f"model={runtime.model_ckpt}, vqgan={runtime.vqgan_ckpt}, unet={runtime.unet_ckpt}, "
        f"python={runtime.python_exe}, sample_step={runtime.sample_step}, gpu_ids={runtime.gpu_ids}"
    )

    return runtime


def _resolve_cpdm_root_dir() -> Path:
    global _cpdm_root_cache

    if _cpdm_root_cache is not None and _is_cpdm_root_dir(_cpdm_root_cache):
        return _cpdm_root_cache

    env_root = _resolve_existing_path(config.CPDM_ROOT_DIR, expect_dir=True)
    if env_root is not None and _is_cpdm_root_dir(env_root):
        _cpdm_root_cache = env_root.resolve()
        return _cpdm_root_cache

    for candidate in _candidate_cpdm_root_dirs():
        if _is_cpdm_root_dir(candidate):
            _cpdm_root_cache = candidate.resolve()
            return _cpdm_root_cache

    raise RuntimeError(
        "CPDM root not found. Set CPDM_ROOT_DIR or place CPDM-main under D:/.../cpdm_model/CPDM-main."
    )


def _candidate_cpdm_root_dirs() -> list[Path]:
    candidates: list[Path] = [
        Path("D:/medical - 副本/cpdm_model/CPDM-main"),
        Path("D:/medical/cpdm_model/CPDM-main"),
        Path("C:/medical - 副本/cpdm_model/CPDM-main"),
        Path("C:/medical/cpdm_model/CPDM-main"),
    ]

    for drive in _existing_drive_roots():
        try:
            top_dirs = [entry for entry in drive.iterdir() if entry.is_dir()]
        except OSError:
            continue

        for top in top_dirs:
            name = top.name.lower()
            if "medical" in name or "cpdm" in name:
                candidates.append(top / "cpdm_model" / "CPDM-main")
            if name == "cpdm_model":
                candidates.append(top / "CPDM-main")

        found = _walk_find_cpdm_root(drive, max_depth=4)
        if found is not None:
            candidates.append(found)

    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate).lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return unique


def _existing_drive_roots() -> list[Path]:
    roots: list[Path] = []
    for letter in "DECF":
        root = Path(f"{letter}:/")
        if root.exists():
            roots.append(root)
    return roots


def _walk_find_cpdm_root(start_root: Path, *, max_depth: int) -> Path | None:
    queue: list[tuple[Path, int]] = [(start_root, 0)]
    skip_names = {
        "$recycle.bin",
        "system volume information",
        "windows",
        "program files",
        "program files (x86)",
    }
    while queue:
        current, depth = queue.pop(0)
        try:
            children = [entry for entry in current.iterdir() if entry.is_dir()]
        except OSError:
            continue

        for child in children:
            child_name = child.name.lower()
            if child_name == "cpdm-main" and _is_cpdm_root_dir(child):
                return child.resolve()
            if depth >= max_depth or child_name in skip_names:
                continue
            queue.append((child, depth + 1))
    return None


def _is_cpdm_root_dir(path: Path) -> bool:
    return path.is_dir() and (path / "main.py").is_file() and (path / "configs").is_dir()


def _resolve_template_config(root_dir: Path) -> Path:
    env_template = _resolve_existing_path(config.CPDM_TEMPLATE_CONFIG, expect_file=True)
    if env_template is not None:
        return env_template

    for candidate in (
        root_dir / "configs" / "Template-CPDM-local-one.yaml",
        root_dir / "configs" / "Template-CPDM.yaml",
    ):
        if candidate.is_file():
            return candidate.resolve()

    raise RuntimeError("CPDM template config not found. Set CPDM_TEMPLATE_CONFIG.")


def _resolve_weight_file(
    *,
    raw_path: str | None,
    root_dir: Path,
    fallback_names: tuple[str, ...],
    title: str,
) -> Path:
    env_weight = _resolve_existing_path(raw_path, expect_file=True)
    if env_weight is not None:
        return env_weight

    for weights_dir in _candidate_weights_dirs(root_dir):
        for filename in fallback_names:
            candidate = weights_dir / filename
            if candidate.is_file():
                return candidate.resolve()

    raise RuntimeError(f"{title} not found. Set .env path or place file under cpdm_weights.")


def _candidate_weights_dirs(root_dir: Path) -> list[Path]:
    candidates = [
        root_dir.parent.parent / "cpdm_weights",
        root_dir.parent / "cpdm_weights",
        root_dir / "cpdm_weights",
        Path("D:/medical - 副本/cpdm_weights"),
        Path("D:/medical/cpdm_weights"),
        Path("C:/medical - 副本/cpdm_weights"),
        Path("C:/medical/cpdm_weights"),
    ]

    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate).lower()
        if key in seen:
            continue
        seen.add(key)
        if candidate.is_dir():
            unique.append(candidate.resolve())
    return unique


def _resolve_python_exe() -> str:
    env_python = _resolve_existing_path(config.CPDM_PYTHON, expect_file=True)
    if env_python is not None:
        return str(env_python)

    candidates = [
        Path("D:/tools/Miniconda/envs/agent310/python.exe"),
        Path("D:/medical - 副本/cpdm_paper/python.exe"),
        Path("C:/medical - 副本/cpdm_paper/python.exe"),
    ]

    conda_prefix = (os.environ.get("CONDA_PREFIX") or "").strip()
    if conda_prefix:
        if os.name == "nt":
            candidates.append(Path(conda_prefix) / "python.exe")
        else:
            candidates.append(Path(conda_prefix) / "bin" / "python")

    for candidate in candidates:
        if candidate.is_file():
            return str(candidate.resolve())
    return "python"


def _resolve_mplconfig_dir(root_dir: Path) -> Path:
    global _warned_invalid_mplconfig

    raw = (config.CPDM_MPLCONFIGDIR or "").strip()
    if raw:
        custom = Path(raw)
        if not custom.is_absolute():
            custom = Path(config.BASE_DIR) / custom
        try:
            custom.mkdir(parents=True, exist_ok=True)
            return custom.resolve()
        except OSError as exc:
            if not _warned_invalid_mplconfig:
                logger.warning(f"[cpdm] ignore invalid CPDM_MPLCONFIGDIR='{raw}': {exc}")
                _warned_invalid_mplconfig = True

    default_dir = root_dir / ".mplconfig"
    default_dir.mkdir(parents=True, exist_ok=True)
    return default_dir.resolve()


def _resolve_existing_path(raw_path: str | None, *, expect_file: bool = False, expect_dir: bool = False) -> Path | None:
    raw = (raw_path or "").strip()
    if not raw:
        return None

    initial = Path(raw)
    candidates = [initial]
    if not initial.is_absolute():
        candidates.append(Path(config.BASE_DIR) / initial)

    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            resolved = candidate
        if not resolved.exists():
            continue
        if expect_file and not resolved.is_file():
            continue
        if expect_dir and not resolved.is_dir():
            continue
        return resolved
    return None

def _run_cpdm_job(
    job_id: str,
    ct_payload: bytes,
    filename: str,
    runtime: CPDMRuntime,
    patient_id: int | None,
    study_id: int | None,
    auth_header: str,
) -> None:
    work_dir = _CPDM_JOB_WORK_ROOT / job_id
    output_dir = _CPDM_OUTPUT_ROOT / job_id
    try:
        backend_mode = use_backend_storage()
        storage_via_backend = backend_mode and bool(patient_id) and bool(study_id)
        if storage_via_backend:
            ensure_storage_context(patient_id, study_id)
        elif backend_mode:
            logger.warning(f"[cpdm] job {job_id} missing patientId/studyId, use local output storage")

        if work_dir.exists():
            shutil.rmtree(work_dir, ignore_errors=True)
        work_dir.mkdir(parents=True, exist_ok=True)

        _set_job(job_id, status="running", progress=5, message="preparing ct input")

        ct_array = _decode_ct_payload(ct_payload, filename, work_dir)
        ct_2d = _to_2d_slice(ct_array)
        ct_prepared = _preprocess_ct(ct_2d)

        dataset_dir = work_dir / "dataset"
        dummy_pet = np.zeros_like(ct_prepared, dtype=np.int16)
        ct_npy_path: Path | None = None

        for stage in ("train", "val", "test"):
            stage_a = dataset_dir / stage / "A"
            stage_b = dataset_dir / stage / "B"
            stage_a.mkdir(parents=True, exist_ok=True)
            stage_b.mkdir(parents=True, exist_ok=True)

            ct_path_stage = stage_a / f"{_INPUT_SAMPLE_NAME}.npy"
            np.save(str(ct_path_stage), ct_prepared)
            np.save(str(stage_b / f"{_INPUT_SAMPLE_NAME}.npy"), dummy_pet)

            if stage == "test":
                ct_npy_path = ct_path_stage

        if ct_npy_path is None:
            raise RuntimeError("failed to prepare test ct input")

        _set_job(job_id, progress=20, message="running attention model")
        attention_dir = work_dir / "cpdm_cache" / "attn_single" / "test"
        attention_dir.mkdir(parents=True, exist_ok=True)
        attention_out = attention_dir / f"{_INPUT_SAMPLE_NAME}.npy"

        _run_attention_inference(runtime, ct_npy_path=ct_npy_path, out_npy=attention_out)

        _set_job(job_id, progress=45, message="running cpdm inference")
        result_root = work_dir / "results"
        job_config = work_dir / "cpdm_runtime.yaml"
        _create_runtime_config(
            runtime=runtime,
            dataset_dir=dataset_dir,
            attention_dir=attention_dir,
            out_config=job_config,
        )
        _run_cpdm_main(runtime=runtime, config_path=job_config, result_root=result_root)

        _set_job(job_id, progress=85, message="collecting outputs")
        pet_npy = _locate_result_npy(result_root=result_root, sample_step=runtime.sample_step)

        if output_dir.exists():
            shutil.rmtree(output_dir, ignore_errors=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        final_meta = output_dir / "meta.json"
        result_payload: dict[str, Any]
        meta: dict[str, Any] = {
            "jobId": job_id,
            "sampleStep": runtime.sample_step,
            "createdAt": time.time(),
            "inputFile": filename,
        }

        if storage_via_backend:
            pet_npy_bytes = pet_npy.read_bytes()
            attention_bytes = attention_out.read_bytes()
            ct_input_bytes = _array_to_npy_bytes(ct_prepared)
            pet_png_bytes = _npy_to_png_bytes(pet_npy)

            pet_png_upload = upload_output_bytes(
                patient_id=int(patient_id),
                study_id=int(study_id),
                filename=f"{job_id}_pet.png",
                file_type="cpdm.pet.png",
                content=pet_png_bytes,
                auth_header=auth_header,
            )
            pet_npy_upload = upload_output_bytes(
                patient_id=int(patient_id),
                study_id=int(study_id),
                filename=f"{job_id}_pet.npy",
                file_type="cpdm.pet.npy",
                content=pet_npy_bytes,
                auth_header=auth_header,
            )
            attention_upload = upload_output_bytes(
                patient_id=int(patient_id),
                study_id=int(study_id),
                filename=f"{job_id}_attention.npy",
                file_type="cpdm.attention.npy",
                content=attention_bytes,
                auth_header=auth_header,
            )
            ct_input_upload = upload_output_bytes(
                patient_id=int(patient_id),
                study_id=int(study_id),
                filename=f"{job_id}_ct_input.npy",
                file_type="cpdm.ct_input.npy",
                content=ct_input_bytes,
                auth_header=auth_header,
            )
            result_payload = {
                "petPngUrl": pet_png_upload.file_path,
                "petNpyUrl": pet_npy_upload.file_path,
                "attentionNpyUrl": attention_upload.file_path,
                "ctInputNpyUrl": ct_input_upload.file_path,
                "sampleStep": runtime.sample_step,
                "storage": "oss",
            }
            meta.update(
                {
                    "storage": "oss",
                    "result": result_payload,
                }
            )
        else:
            final_pet_npy = output_dir / "pet.npy"
            final_pet_png = output_dir / "pet.png"
            final_attention = output_dir / "attention.npy"
            final_ct = output_dir / "ct_input.npy"

            shutil.copy2(str(pet_npy), str(final_pet_npy))
            shutil.copy2(str(attention_out), str(final_attention))
            np.save(str(final_ct), ct_prepared)
            _npy_to_png(final_pet_npy, final_pet_png)

            result_payload = {
                "petPngUrl": f"/api/cpdm/outputs/{job_id}/pet.png",
                "sampleStep": runtime.sample_step,
                "storage": "local",
            }
            meta.update(
                {
                    "storage": "local",
                    "resultNpy": str(final_pet_npy.name),
                    "resultPng": str(final_pet_png.name),
                    "attentionNpy": str(final_attention.name),
                    "result": result_payload,
                }
            )

        final_meta.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        _set_job(
            job_id,
            status="completed",
            progress=100,
            message="completed",
            output=result_payload,
            error=None,
        )
    except Exception as exc:
        logger.error(f"[cpdm] job {job_id} failed: {exc}")
        _set_job(
            job_id,
            status="failed",
            progress=100,
            message="failed",
            error=str(exc),
            output=None,
        )
    finally:
        if not config.CPDM_KEEP_JOB_DIR:
            shutil.rmtree(work_dir, ignore_errors=True)


def _decode_ct_payload(payload: bytes, filename: str, work_dir: Path) -> np.ndarray:
    suffix = Path(filename or "").suffix.lower()
    if suffix == ".npy":
        return np.asarray(np.load(BytesIO(payload), allow_pickle=True))

    temp_input = work_dir / f"input{suffix or '.bin'}"
    temp_input.write_bytes(payload)

    if suffix == ".nrrd":
        import nrrd

        arr, _ = nrrd.read(str(temp_input))
        return np.asarray(arr)

    if suffix in {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}:
        img = Image.open(str(temp_input)).convert("F")
        return np.asarray(img, dtype=np.float32)

    # fallback as npy if extension is unknown
    try:
        return np.asarray(np.load(str(temp_input), allow_pickle=True))
    except Exception as exc:
        raise ValueError(f"unsupported ct file type: {suffix or 'unknown'}") from exc


def _to_2d_slice(arr: np.ndarray) -> np.ndarray:
    x = np.asarray(arr, dtype=np.float32)
    x = np.squeeze(x)
    if x.ndim == 2:
        return x
    if x.ndim == 3:
        # Prefer depth-first volumes: [D, H, W]
        if x.shape[0] >= 8:
            return x[x.shape[0] // 2]
        # Channel-last or depth-last fallback
        return x[:, :, x.shape[2] // 2]
    raise ValueError(f"CT payload must be 2D/3D array, got shape={x.shape}")


def _preprocess_ct(ct_2d: np.ndarray) -> np.ndarray:
    x = np.asarray(ct_2d, dtype=np.float32)
    if np.nanmax(x) <= 1.5:
        x = x * 2047.0
    elif np.nanmin(x) < -200:
        x = np.clip(x, -1024.0, 1023.0) + 1024.0

    x = np.nan_to_num(x, nan=0.0, posinf=2047.0, neginf=0.0)
    x = np.clip(x, 0.0, 2047.0)

    image = Image.fromarray(x, mode="F")
    image = image.resize((256, 256), resample=Image.BILINEAR)
    x256 = np.asarray(image, dtype=np.float32)
    x256 = np.clip(x256, 0.0, 2047.0)
    return x256.astype(np.int16)


def _run_attention_inference(runtime: CPDMRuntime, ct_npy_path: Path, out_npy: Path) -> None:
    script = Path(config.BASE_DIR) / "segmentation_model" / "scripts" / "predict_cpdm_attention.py"
    if not script.exists():
        raise FileNotFoundError(f"CPDM attention script not found: {script}")

    cmd = [
        runtime.python_exe,
        str(script),
        "--ct_npy",
        str(ct_npy_path),
        "--ckpt",
        str(runtime.unet_ckpt),
        "--out_npy",
        str(out_npy),
        "--device",
        "cpu" if runtime.gpu_ids == "-1" else "cuda",
    ]
    env = os.environ.copy()
    env["MPLCONFIGDIR"] = str(runtime.mplconfigdir)
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD", "1")

    _run_command(
        cmd,
        cwd=Path(config.BASE_DIR),
        timeout_seconds=runtime.timeout_seconds,
        env=env,
    )


def _create_runtime_config(runtime: CPDMRuntime, dataset_dir: Path, attention_dir: Path, out_config: Path) -> None:
    cfg_text = runtime.template_config.read_text(encoding="utf-8")
    cfg = yaml.load(cfg_text, Loader=yaml.FullLoader)

    cfg["data"]["dataset_config"]["dataset_path"] = _to_posix(dataset_dir)
    cfg["data"]["test"]["batch_size"] = 1

    cfg["model"]["VQGAN"]["params"]["ckpt_path"] = _to_posix(runtime.vqgan_ckpt)
    cfg["model"]["attention_map_train_path"] = _to_posix(attention_dir)
    cfg["model"]["attention_map_val_path"] = _to_posix(attention_dir)
    cfg["model"]["BB"]["params"]["sample_step"] = int(runtime.sample_step)

    out_config.write_text(yaml.dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _run_cpdm_main(runtime: CPDMRuntime, config_path: Path, result_root: Path) -> None:
    compat_script = Path(config.BASE_DIR) / "segmentation_model" / "scripts" / "run_cpdm_main_compat.py"
    if not compat_script.exists():
        raise FileNotFoundError(f"CPDM compat launcher not found: {compat_script}")

    cmd = [
        runtime.python_exe,
        str(compat_script),
        "--cpdm_root",
        str(runtime.root_dir),
        "--",
        "-c",
        str(config_path),
        "-r",
        str(result_root),
        "--sample_to_eval",
        "--resume_model",
        str(runtime.model_ckpt),
        "--gpu_ids",
        runtime.gpu_ids,
    ]

    env = os.environ.copy()
    env["MPLCONFIGDIR"] = str(runtime.mplconfigdir)
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD", "1")

    _run_command(
        cmd,
        cwd=runtime.root_dir,
        timeout_seconds=runtime.timeout_seconds,
        env=env,
    )


def _run_command(
    cmd: list[str],
    *,
    cwd: Path,
    timeout_seconds: int,
    env: dict[str, str] | None = None,
) -> None:
    logger.info(f"[cpdm] run: {' '.join(cmd)} (cwd={cwd})")
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        timeout=timeout_seconds,
        env=env,
    )
    if proc.returncode != 0:
        stdout = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()
        raise RuntimeError(f"CPDM command failed ({proc.returncode}):\n{stdout}\n{stderr}".strip())


def _locate_result_npy(result_root: Path, sample_step: int) -> Path:
    expected = result_root / "CT2PET_translation" / "CPDM" / "sample_to_eval" / str(sample_step) / f"{_INPUT_SAMPLE_NAME}.npy"
    if expected.exists():
        return expected

    sample_step_str = str(sample_step)
    candidates = [
        p
        for p in result_root.rglob(f"{_INPUT_SAMPLE_NAME}.npy")
        if p.parent.name == sample_step_str
    ]
    if candidates:
        return sorted(candidates)[-1]

    raise FileNotFoundError(f"CPDM result npy not found under {result_root}")


def _array_to_npy_bytes(arr: np.ndarray) -> bytes:
    buf = BytesIO()
    np.save(buf, arr)
    return buf.getvalue()


def _npy_to_png(npy_path: Path, out_png: Path) -> None:
    out_png.write_bytes(_npy_to_png_bytes(npy_path))


def _npy_to_png_bytes(npy_path: Path) -> bytes:
    arr = np.asarray(np.load(str(npy_path), allow_pickle=True), dtype=np.float32).squeeze()
    if arr.ndim != 2:
        raise ValueError(f"Result npy must be 2D after squeeze, got shape={arr.shape}")

    lo, hi = np.percentile(arr, [1.0, 99.0])
    if hi <= lo:
        norm = np.zeros_like(arr, dtype=np.float32)
    else:
        norm = np.clip((arr - lo) / (hi - lo), 0.0, 1.0)

    image = Image.fromarray((norm * 255.0).astype(np.uint8), mode="L")
    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def _to_posix(path: Path) -> str:
    return path.resolve().as_posix()












