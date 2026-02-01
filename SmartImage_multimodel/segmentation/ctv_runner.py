import subprocess
import sys
import tempfile
from pathlib import Path

from utils import logger
import config

_MODALITIES = ("MR_Flair", "MR_T1", "MR_T1c", "MR_T2")


def _resolve_ctv_model_dir() -> Path:
    if config.CTV_MODEL_DIR:
        path = Path(config.CTV_MODEL_DIR)
    else:
        path = Path(config.BASE_DIR) / "segmentation_model"
    if not path.exists():
        raise FileNotFoundError(f"CTV model dir not found: {path}")
    return path


def _resolve_python_exe() -> str:
    return config.CTV_PYTHON or sys.executable


def _resolve_refine_script(model_dir: Path) -> Path:
    if config.CTV_REFINE_SCRIPT:
        return Path(config.CTV_REFINE_SCRIPT)
    return model_dir / "scripts" / "predict_refinement.py"


def _resolve_expand_script(model_dir: Path) -> Path:
    if config.CTV_EXPAND_SCRIPT:
        return Path(config.CTV_EXPAND_SCRIPT)
    return model_dir / "scripts" / "predict_ctv_expansion.py"


def _resolve_conf_script(model_dir: Path) -> Path:
    if config.CTV_CONF_SCRIPT:
        return Path(config.CTV_CONF_SCRIPT)
    return model_dir / "scripts" / "predict_confidence.py"


def _resolve_refine_ckpt(model_dir: Path) -> Path:
    if config.CTV_REFINE_CKPT:
        return Path(config.CTV_REFINE_CKPT)
    return model_dir / "best_refinement(dice=0.9013).pth"


def _resolve_unet_ckpt(model_dir: Path) -> Path:
    if config.CTV_UNET_CKPT:
        return Path(config.CTV_UNET_CKPT)
    return model_dir / "best_lightweight_unet.pth"


def _write_modalities(data_dir: Path, payloads: dict, filenames: dict | None = None) -> None:
    filenames = filenames or {}
    for key in _MODALITIES:
        payload = payloads.get(key)
        if not payload:
            raise ValueError(f"Missing modality payload: {key}")
        raw_name = filenames.get(key) or f"{key}.nrrd"
        name = raw_name if key in raw_name else f"{key}_{raw_name}"
        if not name.lower().endswith(".nrrd"):
            name = name + ".nrrd"
        (data_dir / name).write_bytes(payload)


def _run_command(cmd: list[str], cwd: Path) -> None:
    logger.info(f"[ctv] run: {' '.join(cmd)} (cwd={cwd})")
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )
    if proc.returncode != 0:
        stdout = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()
        raise RuntimeError(f"CTV command failed: {stdout}\n{stderr}".strip())
    if proc.stdout:
        logger.info(f"[ctv] stdout:\n{proc.stdout.strip()}")
    if proc.stderr:
        logger.info(f"[ctv] stderr:\n{proc.stderr.strip()}")


def ctv_refine_multimodal_bytes(payloads: dict, filenames: dict | None = None) -> bytes:
    model_dir = _resolve_ctv_model_dir()
    python_exe = _resolve_python_exe()
    refine_script = _resolve_refine_script(model_dir)
    unet_ckpt = _resolve_unet_ckpt(model_dir)
    refine_ckpt = _resolve_refine_ckpt(model_dir)

    if not refine_script.exists():
        raise FileNotFoundError(f"CTV refine script not found: {refine_script}")
    if not unet_ckpt.exists():
        raise FileNotFoundError(f"CTV UNet checkpoint not found: {unet_ckpt}")
    if not refine_ckpt.exists():
        raise FileNotFoundError(f"CTV refine checkpoint not found: {refine_ckpt}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        data_dir = tmpdir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        _write_modalities(data_dir, payloads, filenames=filenames)
        out_path = tmpdir / "pred_refined.nrrd"
        cmd = [
            python_exe,
            str(refine_script),
            "--data_dir",
            str(data_dir),
            "--out",
            str(out_path),
            "--all_slices",
            "--ckpt_unet",
            str(unet_ckpt),
            "--ckpt_refine",
            str(refine_ckpt),
        ]
        if config.CTV_DEVICE:
            cmd.extend(["--device", config.CTV_DEVICE])
        _run_command(cmd, cwd=model_dir)
        if not out_path.exists():
            raise FileNotFoundError("CTV refine output not found")
        return out_path.read_bytes()


def ctv_expand_multimodal_bytes(payloads: dict, filenames: dict | None = None) -> bytes:
    model_dir = _resolve_ctv_model_dir()
    python_exe = _resolve_python_exe()
    expand_script = _resolve_expand_script(model_dir)

    if not expand_script.exists():
        raise FileNotFoundError(f"CTV expand script not found: {expand_script}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        data_dir = tmpdir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        _write_modalities(data_dir, payloads, filenames=filenames)

        refined_path = tmpdir / "pred_refined.nrrd"
        refined_bytes = ctv_refine_multimodal_bytes(payloads, filenames=filenames)
        refined_path.write_bytes(refined_bytes)

        out_path = tmpdir / "ctv.nrrd"
        cmd = [
            python_exe,
            str(expand_script),
            "--gtv",
            str(refined_path),
            "--out",
            str(out_path),
            "--expansion_mm",
            str(config.CTV_EXPANSION_MM),
        ]
        if config.CTV_SPACING_MM:
            cmd.extend(["--spacing", str(config.CTV_SPACING_MM)])
        if config.CTV_DEVICE:
            cmd.extend(["--device", config.CTV_DEVICE])
        _run_command(cmd, cwd=model_dir)
        if not out_path.exists():
            raise FileNotFoundError("CTV expand output not found")
        return out_path.read_bytes()


def ctv_confidence_multimodal_png(payloads: dict, filenames: dict | None = None) -> bytes:
    model_dir = _resolve_ctv_model_dir()
    python_exe = _resolve_python_exe()
    conf_script = _resolve_conf_script(model_dir)
    unet_ckpt = _resolve_unet_ckpt(model_dir)

    if not conf_script.exists():
        raise FileNotFoundError(f"CTV confidence script not found: {conf_script}")
    if not unet_ckpt.exists():
        raise FileNotFoundError(f"CTV UNet checkpoint not found: {unet_ckpt}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        data_dir = tmpdir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        _write_modalities(data_dir, payloads, filenames=filenames)

        out_png = tmpdir / f"confidence_{int(config.CTV_CONF_SLICE_INDEX)}.png"
        out_nrrd = tmpdir / "confidence.nrrd"
        cmd = [
            python_exe,
            str(conf_script),
            "--data_dir",
            str(data_dir),
            "--slice_index",
            str(int(config.CTV_CONF_SLICE_INDEX)),
            "--out_png",
            str(out_png),
            "--out_nrrd",
            str(out_nrrd),
            "--ckpt",
            str(unet_ckpt),
        ]
        if config.CTV_CONF_NORMALIZE:
            cmd.append("--normalize")
        if config.CTV_DEVICE:
            cmd.extend(["--device", config.CTV_DEVICE])
        _run_command(cmd, cwd=model_dir)
        if not out_png.exists():
            if out_nrrd.exists():
                _render_confidence_png(out_nrrd, out_png)
        if not out_png.exists():
            raise FileNotFoundError("CTV confidence PNG output not found")
        return out_png.read_bytes()


def _render_confidence_png(nrrd_path: Path, out_png: Path) -> None:
    try:
        import nrrd
        import numpy as np
    except Exception as exc:
        raise RuntimeError("pynrrd is required to render confidence PNG") from exc
    try:
        import matplotlib.pyplot as plt
    except Exception as exc:
        raise RuntimeError("matplotlib is required to render confidence PNG") from exc

    data, _hdr = nrrd.read(str(nrrd_path))
    arr = np.asarray(data, dtype=np.float32)
    vmin, vmax = float(arr.min()), float(arr.max())
    if vmax - vmin > 1e-8:
        norm = (arr - vmin) / (vmax - vmin)
    else:
        norm = arr
    fig, ax = plt.subplots(figsize=(8, 8))
    im = ax.imshow(norm, cmap="jet", vmin=0, vmax=1)
    ax.axis("off")
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    plt.tight_layout()
    fig.savefig(str(out_png), dpi=150)
    plt.close(fig)
