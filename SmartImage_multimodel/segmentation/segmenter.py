import sys
import tempfile
import threading
from pathlib import Path

import numpy as np

from utils import logger
import config

_MODEL_LOCK = threading.Lock()
_MODEL_BUNDLE = None
_MODALITIES = ("MR_Flair", "MR_T1", "MR_T1c", "MR_T2")


def _load_nrrd(path):
    # Prefer SimpleITK if available to preserve metadata
    try:
        import SimpleITK as sitk
    except Exception:
        sitk = None

    if sitk is not None:
        img = sitk.ReadImage(str(path))
        arr = sitk.GetArrayFromImage(img)  # z,y,x for 3D; y,x for 2D
        meta = ("sitk", img)
        return arr, meta

    # Fallback to pynrrd
    try:
        import nrrd
    except Exception as e:
        raise RuntimeError(
            "Neither SimpleITK nor pynrrd is available. Install one of them to read NRRD."
        ) from e

    arr, hdr = nrrd.read(str(path))
    meta = ("nrrd", hdr)
    return arr, meta


def _save_nrrd(arr, meta, path):
    kind, obj = meta
    if kind == "sitk":
        import SimpleITK as sitk
        out = sitk.GetImageFromArray(arr)
        out.CopyInformation(obj)
        sitk.WriteImage(out, str(path))
        return

    import nrrd
    nrrd.write(str(path), arr, obj)


def _normalize_percentile(arr, low=1.0, high=99.0):
    arr = arr.astype(np.float32)
    lo, hi = np.nanpercentile(arr, [low, high])
    arr = np.clip(arr, lo, hi)
    arr = arr - arr.min()
    denom = arr.max()
    if denom > 1e-8:
        arr = arr / denom
    return arr


def _normalize_modalities(vol, low=1.0, high=99.0):
    if vol.ndim == 4:
        out = np.empty_like(vol, dtype=np.float32)
        for c in range(vol.shape[0]):
            out[c] = _normalize_percentile(vol[c], low=low, high=high)
        return out
    return _normalize_percentile(vol, low=low, high=high)


def _find_nrrd(data_dir: Path, stem: str) -> Path:
    for f in data_dir.glob(f"*{stem}*.nrrd"):
        return f
    raise FileNotFoundError(f"在 {data_dir} 下未找到包含 '{stem}' 的 .nrrd 文件")


def _load_four_modalities(data_dir: Path):
    vols = []
    paths = []
    meta = None
    for m in _MODALITIES:
        p = _find_nrrd(data_dir, m)
        arr, mmeta = _load_nrrd(p)
        vols.append(np.asarray(arr, dtype=np.float32))
        paths.append(p)
        if meta is None:
            meta = mmeta
    s0 = vols[0].shape
    for i, v in enumerate(vols[1:], 1):
        if v.shape != s0:
            raise ValueError(
                f"模态 {_MODALITIES[i]} 形状 {v.shape} 与 {_MODALITIES[0]} {s0} 不一致"
            )
    return np.stack(vols, axis=0), meta, paths


def _predict_slice(model, device, slice_2d, in_channels, model_kind):
    import torch

    if slice_2d.ndim == 2:
        x = torch.from_numpy(slice_2d[None, None, ...]).to(device)
        if model_kind == "nnunet":
            zeros = torch.zeros_like(x)
            x = torch.cat([x, zeros, zeros], dim=1)
        elif in_channels > 1:
            x = x.repeat(1, in_channels, 1, 1)
    elif slice_2d.ndim == 3:
        x = torch.from_numpy(slice_2d[None, ...]).to(device)
        if model_kind == "nnunet" and x.shape[1] != in_channels:
            raise ValueError(f"NNUNet expects {in_channels} channels, got {x.shape[1]}")
    else:
        raise ValueError(f"Unsupported slice dims: {slice_2d.shape}")
    with torch.no_grad():
        if model_kind == "lightweight":
            logits, _conf = model(x)
        else:
            logits = model(x)
        pred = torch.argmax(torch.softmax(logits, dim=1), dim=1)
    return pred.squeeze(0).cpu().numpy().astype(np.uint8)


def _resolve_model_dir():
    if config.SEG_MODEL_DIR:
        return Path(config.SEG_MODEL_DIR)
    # Fallback to demo path if present
    demo = Path(r"C:\Users\hu196\Desktop\SmartImage\model")
    return demo if demo.exists() else None


def _resolve_weights_path(model_dir):
    if config.SEG_WEIGHTS_PATH:
        return Path(config.SEG_WEIGHTS_PATH)
    if model_dir is None:
        return None
    candidates = [
        model_dir / "best_refinement(dice=0.9013).pth",
        model_dir / "best_lightweight_unet.pth",
    ]
    for cand in candidates:
        if cand.exists():
            return cand
    return None


def _ensure_model():
    global _MODEL_BUNDLE
    if _MODEL_BUNDLE is not None:
        return _MODEL_BUNDLE

    with _MODEL_LOCK:
        if _MODEL_BUNDLE is not None:
            return _MODEL_BUNDLE

        import torch

        model_dir = _resolve_model_dir()
        if model_dir and model_dir.exists():
            sys.path.insert(0, str(model_dir))
            nested = model_dir / "models"
            if nested.exists():
                sys.path.insert(0, str(nested))
                deeper = nested / "models"
                if deeper.exists():
                    sys.path.insert(0, str(deeper))

        weights_path = _resolve_weights_path(model_dir)
        if not weights_path or not weights_path.exists():
            raise FileNotFoundError(
                "Segmentation weights not found. Set SEG_WEIGHTS_PATH to the .pth file."
            )

        device = torch.device(config.SEG_DEVICE or "cpu")
        state = torch.load(str(weights_path), map_location=device)
        if isinstance(state, dict) and "model_state_dict" in state:
            state = state["model_state_dict"]

        # Decide model type based on checkpoint keys
        state_keys = set(state.keys()) if isinstance(state, dict) else set()
        is_nnunet = any(k.startswith("enc1.") for k in state_keys) or "final.weight" in state_keys
        is_light = any(k.startswith("inc.double_conv.") for k in state_keys) or "outc.weight" in state_keys

        model_kind = "nnunet" if is_nnunet and not is_light else "lightweight"

        LightweightUNet = None
        NNUNetRefinement = None
        if model_kind == "lightweight":
            try:
                from models.models.lightweight_unet import LightweightUNet
            except Exception:
                try:
                    from models.lightweight_unet import LightweightUNet
                except Exception:
                    try:
                        from lightweight_unet import LightweightUNet
                    except Exception:
                        LightweightUNet = None
        if model_kind == "nnunet":
            try:
                from models.models.nnunet_refinement import NNUNetRefinement
            except Exception:
                try:
                    from models.nnunet_refinement import NNUNetRefinement
                except Exception:
                    try:
                        from nnunet_refinement import NNUNetRefinement
                    except Exception:
                        NNUNetRefinement = None

        if model_kind == "lightweight" and LightweightUNet is None:
            raise RuntimeError(
                "Failed to import LightweightUNet. Set SEG_MODEL_DIR to the demo model folder."
            )
        if model_kind == "nnunet" and NNUNetRefinement is None:
            raise RuntimeError(
                "Failed to import NNUNetRefinement. Set SEG_MODEL_DIR to the demo model folder."
            )

        in_channels = 1
        n_classes = 2
        if isinstance(state, dict):
            if model_kind == "lightweight":
                w_in = state.get("inc.double_conv.0.weight")
                w_out = state.get("outc.weight")
                if w_in is not None:
                    in_channels = int(w_in.shape[1])
                if w_out is not None:
                    n_classes = int(w_out.shape[0])
            else:
                w_in = state.get("enc1.0.conv.0.weight")
                w_out = state.get("final.weight")
                if w_in is not None:
                    in_channels = int(w_in.shape[1])
                if w_out is not None:
                    n_classes = int(w_out.shape[0])

        if model_kind == "lightweight":
            model = LightweightUNet(n_channels=in_channels, n_classes=n_classes)
        else:
            model = NNUNetRefinement(in_channels=in_channels, n_classes=n_classes)

        model.load_state_dict(state)
        model.to(device)
        model.eval()

        logger.info(
            f"[seg] model loaded kind={model_kind} weights={weights_path} device={device} in_channels={in_channels} classes={n_classes}"
        )
        _MODEL_BUNDLE = (model, device, in_channels, model_kind)
        return _MODEL_BUNDLE


def _segment_volume(vol, meta):
    model, device, in_channels, model_kind = _ensure_model()
    logger.info(f"[seg] input shape={vol.shape} dtype={vol.dtype}")

    if in_channels == 4:
        if vol.ndim == 4:
            if vol.shape[0] == 4:
                pass
            elif vol.shape[-1] == 4:
                vol = np.moveaxis(vol, -1, 0)
            else:
                raise ValueError(f"Expected 4-channel NRRD, got shape={vol.shape}")
        elif vol.ndim == 3:
            data_dir = Path(config.SEG_MODALITY_DIR) if config.SEG_MODALITY_DIR else None
            if data_dir and data_dir.exists():
                vol, meta, paths = _load_four_modalities(data_dir)
                logger.info(f"[seg] loaded 4 modalities from {data_dir}: {[p.name for p in paths]}")
            else:
                raise ValueError(
                    "Model expects 4-channel input, but only single NRRD was provided. "
                    "Set SEG_MODALITY_DIR to a folder containing MR_Flair/MR_T1/MR_T1c/MR_T2."
                )
        else:
            raise ValueError(f"Unsupported NRRD dims: {vol.shape}")

    vol = _normalize_modalities(vol)
    logger.info(
        f"[seg] input norm stats mean={float(np.mean(vol)):.4f} std={float(np.std(vol)):.4f} min={float(np.min(vol)):.4f} max={float(np.max(vol)):.4f}"
    )

    if vol.ndim == 2:
        pred = _predict_slice(model, device, vol, in_channels, model_kind)
    elif vol.ndim == 3:
        preds = []
        for i in range(vol.shape[0]):
            preds.append(_predict_slice(model, device, vol[i], in_channels, model_kind))
        pred = np.stack(preds, axis=0)
    elif vol.ndim == 4:
        preds = []
        for i in range(vol.shape[1]):
            sl = vol[:, i, :, :]
            preds.append(_predict_slice(model, device, sl, in_channels, model_kind))
        pred = np.stack(preds, axis=0)
    else:
        raise ValueError(f"Unsupported NRRD dims: {vol.shape}")

    if config.SEG_LABEL_CLASS is not None:
        pred = (pred == int(config.SEG_LABEL_CLASS)).astype(np.uint8)

    unique, counts = np.unique(pred, return_counts=True)
    stats = {int(k): int(v) for k, v in zip(unique, counts)}
    nonzero = int((pred > 0).sum())
    total = int(pred.size)
    logger.info(f"[seg] output stats labels={stats} nonzero={nonzero}/{total}")
    return pred, meta


def segment_nrrd_file(input_path: Path, output_path: Path):
    arr, meta = _load_nrrd(input_path)
    pred, meta = _segment_volume(arr, meta)
    _save_nrrd(pred, meta, output_path)


def segment_nrrd_bytes(payload: bytes, filename: str = None) -> bytes:
    if not payload:
        raise ValueError("Empty NRRD payload")

    name = filename or "input.nrrd"
    if not name.lower().endswith(".nrrd"):
        name = name + ".nrrd"

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        input_path = tmpdir / name
        output_path = tmpdir / "label.nrrd"
        input_path.write_bytes(payload)
        segment_nrrd_file(input_path, output_path)
        return output_path.read_bytes()


def segment_multimodal_nrrd_bytes(payloads: dict, filenames: dict = None) -> bytes:
    if not payloads:
        raise ValueError("Empty multimodal payloads")
    filenames = filenames or {}
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        volumes = []
        meta = None
        for key in _MODALITIES:
            payload = payloads.get(key)
            if not payload:
                raise ValueError(f"Missing modality: {key}")
            name = filenames.get(key) or f"{key}.nrrd"
            if not name.lower().endswith(".nrrd"):
                name = name + ".nrrd"
            path = tmpdir / name
            path.write_bytes(payload)
            arr, mmeta = _load_nrrd(path)
            volumes.append(np.asarray(arr, dtype=np.float32))
            if meta is None:
                meta = mmeta
        s0 = volumes[0].shape
        for i, v in enumerate(volumes[1:], 1):
            if v.shape != s0:
                raise ValueError(
                    f"Modality {_MODALITIES[i]} shape {v.shape} != {_MODALITIES[0]} {s0}"
                )
        vol = np.stack(volumes, axis=0)
        pred, meta = _segment_volume(vol, meta)
        output_path = tmpdir / "label.nrrd"
        _save_nrrd(pred, meta, output_path)
        return output_path.read_bytes()
