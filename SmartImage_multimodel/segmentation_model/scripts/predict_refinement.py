"""
NNUNet Refinement 预测脚本

两阶段流程：
  1. LightweightUNet 生成初稿 + 置信度
  2. NNUNetRefinement 精细修正

用法:
  python predict_refinement.py --data_dir data --out pred_refined.nrrd --all_slices
  python predict_refinement.py --data_dir data --ckpt_unet best_lightweight_unet.pth --ckpt_refine "best_refinement(dice=0.9013).pth"
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

try:
    import nrrd
except ImportError:
    raise SystemExit("请安装 pynrrd: pip install pynrrd")

# 从当前包加载模型
if __name__ == "__main__" and __package__ is None:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lightweight_unet import LightweightUNet
from nnunet_refinement import NNUNetRefinement

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


def main() -> None:
    ap = argparse.ArgumentParser(description="NNUNet Refinement 两阶段预测")
    ap.add_argument("--data_dir", type=str, default="data", help="NRRD 所在目录")
    ap.add_argument("--modality", type=str, default="MR_T1c", choices=MODALITIES,
                    help="1 通道 UNet 时使用的模态")
    ap.add_argument("--ckpt_unet", type=str, default="best_lightweight_unet.pth",
                    help="LightweightUNet 权重路径")
    ap.add_argument("--ckpt_refine", type=str, default="best_refinement(dice=0.9013).pth",
                    help="NNUNetRefinement 权重路径")
    ap.add_argument("--out", type=str, default="pred_refined.nrrd", help="输出 NRRD 路径")
    ap.add_argument("--slice_axis", type=int, default=3, help="切片轴；(C,H,W,D) 中 3=D 为深度")
    ap.add_argument("--slice_index", type=int, default=-1, help="切片索引，-1 为中间层")
    ap.add_argument("--all_slices", action="store_true", help="逐层预测输出 3D NRRD")
    ap.add_argument("--device", type=str, default="", help="cuda / cpu")
    args = ap.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.is_dir():
        raise SystemExit(f"目录不存在: {data_dir}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if args.device:
        device = torch.device(args.device)
    print(f"使用设备: {device}")

    ckpt_unet = Path(args.ckpt_unet)
    ckpt_refine = Path(args.ckpt_refine)
    if not ckpt_unet.is_file():
        raise SystemExit(f"UNet 权重不存在: {ckpt_unet}")
    if not ckpt_refine.is_file():
        raise SystemExit(f"Refinement 权重不存在: {ckpt_refine}")

    # ---------- 加载 LightweightUNet ----------
    state_unet = load_checkpoint(ckpt_unet)
    key = "inc.double_conv.0.weight"
    if key not in state_unet:
        raise SystemExit(f"UNet 权重缺少 {key}")
    n_channels_unet = int(state_unet[key].shape[1])
    print(f"加载 LightweightUNet (n_channels={n_channels_unet}) ...")
    model_unet = LightweightUNet(n_channels=n_channels_unet, n_classes=2)
    model_unet.load_state_dict(state_unet, strict=True)
    model_unet = model_unet.to(device).eval()

    # ---------- 加载 NNUNetRefinement ----------
    state_refine = load_checkpoint(ckpt_refine)
    # 检测 in_channels
    key_refine = "enc1.0.conv.0.weight"
    if key_refine not in state_refine:
        raise SystemExit(f"Refinement 权重缺少 {key_refine}")
    in_channels_refine = int(state_refine[key_refine].shape[1])
    print(f"加载 NNUNetRefinement (in_channels={in_channels_refine}) ...")
    model_refine = NNUNetRefinement(in_channels=in_channels_refine, n_classes=2)
    model_refine.load_state_dict(state_refine, strict=True)
    model_refine = model_refine.to(device).eval()

    # ---------- 加载数据 ----------
    if n_channels_unet == 1:
        print(f"加载单模态: {args.modality} ...")
        vol, _ = load_single_modality(data_dir, args.modality)
    else:
        print("加载四模态 (Flair, T1, T1c, T2) ...")
        vol, _ = load_four_modalities(data_dir)

    vol = normalize_modalities(vol)
    axis = args.slice_axis
    n_slices = vol.shape[axis]
    print(f"  数据形状: {vol.shape}, 切片轴={axis}, 共 {n_slices} 层")

    # 用于 Refinement 输入的图像：取第一个通道或取平均
    if vol.shape[0] == 1:
        vol_single = vol  # (1, D, H, W)
    else:
        vol_single = vol.mean(axis=0, keepdims=True).astype(np.float32)

    out_path = Path(args.out)

    # 边界保护参数
    INPUT_THRESH = 0.01   # 输入均值低于此值认为是空切片
    OUTPUT_RATIO = 0.15   # 预测前景占比超过此值认为异常

    def predict_slice(idx: int) -> tuple[np.ndarray, bool]:
        """对单层做两阶段预测，返回 (H, W) uint8 和是否跳过标志。"""
        # 取切片
        sl_unet = slice_at(vol, axis, idx)        # (C, H, W) for UNet
        sl_single = slice_at(vol_single, axis, idx)  # (1, H, W) for Refinement image

        # 边界保护：输入几乎为空则跳过
        if sl_single.mean() < INPUT_THRESH:
            return np.zeros(sl_single.shape[1:], dtype=np.uint8), True

        t_unet = torch.from_numpy(sl_unet).float().unsqueeze(0).to(device)  # (1, C, H, W)
        t_single = torch.from_numpy(sl_single).float().unsqueeze(0).to(device)  # (1, 1, H, W)

        # 阶段 1: UNet 生成初稿 + 置信度
        with torch.no_grad():
            logits, confidence = model_unet(t_unet)
            probs = F.softmax(logits, dim=1)
            init_mask = probs[:, 1:2, :, :]  # 取类别 1 的概率作为 mask (1,1,H,W)

        # 阶段 2: Refinement
        # 输入: image(1) + init_mask(1) + confidence(1) = 3 通道
        refine_input = torch.cat([t_single, init_mask, confidence], dim=1)  # (1,3,H,W)
        with torch.no_grad():
            refine_logits = model_refine(refine_input)
            refine_probs = F.softmax(refine_logits, dim=1)
            pred = torch.argmax(refine_probs, dim=1)  # (1, H, W)

        pred_np = pred.cpu().numpy()[0].astype(np.uint8)

        # 边界保护：预测前景占比异常则置零
        fg_ratio = pred_np.sum() / pred_np.size
        if fg_ratio > OUTPUT_RATIO:
            return np.zeros_like(pred_np), True

        return pred_np, False

    if args.all_slices:
        print("逐层两阶段预测，输出 3D ...")
        pred_3d = np.zeros((vol.shape[1], vol.shape[2], vol.shape[3]), dtype=np.uint8)
        skipped = 0
        for idx in range(n_slices):
            arr, was_skipped = predict_slice(idx)
            if was_skipped:
                skipped += 1
            if axis == 1:
                pred_3d[idx, :, :] = arr
            elif axis == 2:
                pred_3d[:, idx, :] = arr
            else:
                pred_3d[:, :, idx] = arr
            if (idx + 1) % 20 == 0 or idx == 0:
                print(f"  切片 {idx + 1}/{n_slices}")
        if out_path.suffix.lower() != ".nrrd":
            out_path = out_path.with_suffix(".nrrd")
        nrrd.write(str(out_path), pred_3d)
        print(f"已保存 3D 预测: {out_path}")
        if skipped > 0:
            print(f"  (跳过 {skipped} 个边界/异常层)")
    else:
        idx = args.slice_index
        if idx < 0:
            idx = n_slices // 2
        print(f"预测单层 (axis={axis}, index={idx}) ...")
        pred_np, _ = predict_slice(idx)
        if out_path.suffix.lower() != ".nrrd":
            out_path = out_path.with_suffix(".nrrd")
        nrrd.write(str(out_path), pred_np)
        print(f"已保存 2D 预测: {out_path}")


if __name__ == "__main__":
    main()
