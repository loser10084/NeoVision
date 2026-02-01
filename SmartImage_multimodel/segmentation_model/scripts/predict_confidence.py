"""
置信度热力图生成脚本

从 LightweightUNet 输出置信度图，保存为 NRRD 和可视化热力图 PNG。

用法:
  python predict_confidence.py --data_dir data --out_nrrd confidence.nrrd --out_png confidence.png
  python predict_confidence.py --data_dir data --all_slices --out_nrrd confidence_3d.nrrd
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

try:
    import nrrd
except ImportError:
    raise SystemExit("请安装 pynrrd: pip install pynrrd")

try:
    from PIL import Image
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm
    HAS_VIS = True
except ImportError:
    HAS_VIS = False

# 从当前包加载模型
if __name__ == "__main__" and __package__ is None:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lightweight_unet import LightweightUNet

MODALITIES = ("MR_Flair", "MR_T1", "MR_T1c", "MR_T2")


def _find_nrrd(data_dir: Path, stem: str) -> Path:
    for f in data_dir.glob(f"*{stem}*.nrrd"):
        return f
    raise FileNotFoundError(f"在 {data_dir} 下未找到包含 '{stem}' 的 .nrrd 文件")


def load_single_modality(data_dir: Path, modality: str) -> tuple[np.ndarray, Path]:
    p = _find_nrrd(data_dir, modality)
    data, _ = nrrd.read(str(p))
    vol = np.asarray(data, dtype=np.float32)
    return vol[np.newaxis, ...], p


def load_four_modalities(data_dir: Path) -> tuple[np.ndarray, list[Path]]:
    vols, paths = [], []
    for m in MODALITIES:
        p = _find_nrrd(data_dir, m)
        data, _ = nrrd.read(str(p))
        vols.append(np.asarray(data, dtype=np.float32))
        paths.append(p)
    s0 = vols[0].shape
    for i, v in enumerate(vols[1:], 1):
        if v.shape != s0:
            raise ValueError(f"模态 {MODALITIES[i]} 形状 {v.shape} 与 {MODALITIES[0]} {s0} 不一致")
    return np.stack(vols, axis=0), paths


def normalize_modalities(x: np.ndarray, low: float = 1.0, high: float = 99.0) -> np.ndarray:
    out = np.empty_like(x, dtype=np.float32)
    for c in range(x.shape[0]):
        v = x[c]
        lo, hi = np.nanpercentile(v, [low, high])
        v = np.clip(v, lo, hi)
        v = v - v.min()
        denom = v.max()
        if denom > 1e-8:
            v = v / denom
        out[c] = v
    return out


def slice_at(x: np.ndarray, axis: int, index: int) -> np.ndarray:
    sl: list[slice | int] = [slice(None)] * x.ndim
    sl[axis] = index
    return np.ascontiguousarray(x[tuple(sl)])


def load_checkpoint(ckpt_path: Path, map_location="cpu") -> dict:
    raw = torch.load(ckpt_path, map_location=map_location)
    if isinstance(raw, dict):
        if "model_state_dict" in raw:
            return raw["model_state_dict"]
        elif "state_dict" in raw:
            return raw["state_dict"]
    return raw


def save_heatmap_png(conf: np.ndarray, out_path: Path, title: str = "Confidence Heatmap",
                     normalize: bool = False) -> None:
    """将 2D 置信度图保存为热力图 PNG。"""
    if not HAS_VIS:
        print("  (跳过 PNG：需安装 matplotlib 和 pillow)")
        return
    
    data = conf.copy()
    if normalize:
        # 归一化到实际 min~max，增强对比度
        vmin, vmax = data.min(), data.max()
        if vmax - vmin > 1e-8:
            data = (data - vmin) / (vmax - vmin)
        label = f"(normalized: {vmin:.3f}~{vmax:.3f})"
    else:
        vmin, vmax = 0, 1
        label = "(raw: 0~1)"
    
    fig, ax = plt.subplots(figsize=(8, 8))
    im = ax.imshow(data, cmap='jet', vmin=0, vmax=1)
    ax.set_title(f"{title}\n{label}")
    ax.axis('off')
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    plt.tight_layout()
    plt.savefig(str(out_path), dpi=150)
    plt.close(fig)
    print(f"  已保存热力图: {out_path}")


def main() -> None:
    ap = argparse.ArgumentParser(description="置信度热力图生成")
    ap.add_argument("--data_dir", type=str, default="data", help="NRRD 所在目录")
    ap.add_argument("--modality", type=str, default="MR_T1c", choices=MODALITIES,
                    help="1 通道时使用的模态")
    ap.add_argument("--ckpt", type=str, default="best_lightweight_unet.pth", help="模型权重路径")
    ap.add_argument("--out_nrrd", type=str, default="confidence.nrrd", help="置信度 NRRD 输出路径")
    ap.add_argument("--out_png", type=str, default="confidence.png", help="热力图 PNG 输出路径（仅单层）")
    ap.add_argument("--slice_axis", type=int, default=3, help="切片轴；(C,H,W,D) 中 3=D")
    ap.add_argument("--slice_index", type=int, default=-1, help="切片索引，-1 为中间层")
    ap.add_argument("--all_slices", action="store_true", help="逐层输出 3D 置信度 NRRD")
    ap.add_argument("--normalize", action="store_true", help="归一化置信度到实际范围，增强颜色对比")
    ap.add_argument("--device", type=str, default="", help="cuda / cpu")
    args = ap.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.is_dir():
        raise SystemExit(f"目录不存在: {data_dir}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if args.device:
        device = torch.device(args.device)
    print(f"使用设备: {device}")

    ckpt_path = Path(args.ckpt)
    if not ckpt_path.is_file():
        raise SystemExit(f"权重文件不存在: {ckpt_path}")

    # ---------- 加载模型 ----------
    state = load_checkpoint(ckpt_path)
    key = "inc.double_conv.0.weight"
    if key not in state:
        raise SystemExit(f"权重缺少 {key}")
    n_channels = int(state[key].shape[1])

    # ---------- 加载数据 ----------
    if n_channels == 1:
        print(f"加载单模态: {args.modality} ...")
        vol, _ = load_single_modality(data_dir, args.modality)
    else:
        print("加载四模态 (Flair, T1, T1c, T2) ...")
        vol, _ = load_four_modalities(data_dir)

    vol = normalize_modalities(vol)
    axis = args.slice_axis
    n_slices = vol.shape[axis]
    print(f"  数据形状: {vol.shape}, 切片轴={axis}, 共 {n_slices} 层")

    print(f"加载模型 (n_channels={n_channels}) ...")
    model = LightweightUNet(n_channels=n_channels, n_classes=2)
    model.load_state_dict(state, strict=True)
    model = model.to(device).eval()

    # 边界保护参数
    INPUT_THRESH = 0.01

    out_nrrd = Path(args.out_nrrd)
    out_png = Path(args.out_png)

    if args.all_slices:
        print("逐层生成 3D 置信度 ...")
        conf_3d = np.zeros((vol.shape[1], vol.shape[2], vol.shape[3]), dtype=np.float32)
        for idx in range(n_slices):
            sl = slice_at(vol, axis, idx)
            if sl.mean() < INPUT_THRESH:
                continue
            t = torch.from_numpy(sl).float().unsqueeze(0).to(device)
            with torch.no_grad():
                _, confidence = model(t)
            conf_np = confidence.cpu().numpy()[0, 0]  # (H, W)
            if axis == 1:
                conf_3d[idx, :, :] = conf_np
            elif axis == 2:
                conf_3d[:, idx, :] = conf_np
            else:
                conf_3d[:, :, idx] = conf_np
            if (idx + 1) % 20 == 0 or idx == 0:
                print(f"  切片 {idx + 1}/{n_slices}")
        if out_nrrd.suffix.lower() != ".nrrd":
            out_nrrd = out_nrrd.with_suffix(".nrrd")
        nrrd.write(str(out_nrrd), conf_3d)
        print(f"已保存 3D 置信度: {out_nrrd}")
    else:
        idx = args.slice_index
        if idx < 0:
            idx = n_slices // 2
        print(f"生成单层置信度 (axis={axis}, index={idx}) ...")
        sl = slice_at(vol, axis, idx)
        t = torch.from_numpy(sl).float().unsqueeze(0).to(device)
        with torch.no_grad():
            logits, confidence = model(t)
        conf_np = confidence.cpu().numpy()[0, 0]  # (H, W)

        # 保存 NRRD
        if out_nrrd.suffix.lower() != ".nrrd":
            out_nrrd = out_nrrd.with_suffix(".nrrd")
        nrrd.write(str(out_nrrd), conf_np.astype(np.float32))
        print(f"已保存置信度 NRRD: {out_nrrd}")

        # 保存热力图 PNG
        save_heatmap_png(conf_np, out_png, title=f"Confidence (slice {idx})",
                         normalize=args.normalize)

    print("\n统计:")
    if args.all_slices:
        print(f"  置信度范围: [{conf_3d.min():.3f}, {conf_3d.max():.3f}]")
        print(f"  置信度均值: {conf_3d.mean():.3f}")
    else:
        print(f"  置信度范围: [{conf_np.min():.3f}, {conf_np.max():.3f}]")
        print(f"  置信度均值: {conf_np.mean():.3f}")


if __name__ == "__main__":
    main()
