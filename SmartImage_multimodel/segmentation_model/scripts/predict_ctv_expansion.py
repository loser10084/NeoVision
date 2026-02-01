"""
CTV 外扩预测脚本

从 GTV 预测结果外扩生成 CTV：
  - 规则外扩：基于形态学膨胀，按指定毫米数外扩
  - 学习型外扩（可选）：使用 LearningBasedExpansion 模型

用法:
  python predict_ctv_expansion.py --gtv pred_3d.nrrd --out ctv.nrrd --expansion_mm 10
  python predict_ctv_expansion.py --gtv pred_refined.nrrd --out ctv.nrrd --expansion_mm 5 --spacing 1.0
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import torch

try:
    import nrrd
except ImportError:
    raise SystemExit("请安装 pynrrd: pip install pynrrd")

# 从当前包加载模块
if __name__ == "__main__" and __package__ is None:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ctv_expansion import RuleBasedExpansion, LearningBasedExpansion, CTVExpansionModule


def load_checkpoint(ckpt_path: Path, map_location="cpu") -> dict:
    raw = torch.load(ckpt_path, map_location=map_location)
    if isinstance(raw, dict):
        if "model_state_dict" in raw:
            return raw["model_state_dict"]
        elif "state_dict" in raw:
            return raw["state_dict"]
    return raw


def main() -> None:
    ap = argparse.ArgumentParser(description="CTV 外扩预测（从 GTV 生成 CTV）")
    ap.add_argument("--gtv", type=str, default="pred_3d.nrrd", help="GTV 预测 NRRD 路径")
    ap.add_argument("--out", type=str, default="ctv.nrrd", help="CTV 输出 NRRD 路径")
    ap.add_argument("--expansion_mm", type=float, default=10.0, help="外扩距离（毫米）")
    ap.add_argument("--spacing", type=float, default=1.0, help="像素间距（毫米/像素）")
    ap.add_argument("--ckpt_learning", type=str, default="", help="学习型外扩模型权重（可选，留空则仅用规则）")
    ap.add_argument("--device", type=str, default="", help="cuda / cpu")
    args = ap.parse_args()

    gtv_path = Path(args.gtv)
    if not gtv_path.is_file():
        raise SystemExit(f"GTV 文件不存在: {gtv_path}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if args.device:
        device = torch.device(args.device)

    # 边界保护参数
    OUTPUT_RATIO = 0.15   # 某层前景占比超过此值认为异常

    # ---------- 加载 GTV ----------
    print(f"加载 GTV: {gtv_path} ...")
    gtv_data, gtv_header = nrrd.read(str(gtv_path))
    gtv_mask = (np.asarray(gtv_data) > 0).astype(np.uint8)
    print(f"  形状: {gtv_mask.shape}, GTV 体素数: {gtv_mask.sum()}")

    # ---------- 边界保护：清理 GTV 中异常层 ----------
    cleaned = 0
    for z in range(gtv_mask.shape[2]):
        sl = gtv_mask[:, :, z]
        fg_ratio = sl.sum() / sl.size
        if fg_ratio > OUTPUT_RATIO:
            gtv_mask[:, :, z] = 0
            cleaned += 1
    if cleaned > 0:
        print(f"  清理 GTV 异常层: {cleaned} 层")

    # ---------- 规则外扩 ----------
    print(f"执行规则外扩: {args.expansion_mm} mm (spacing={args.spacing} mm/pixel) ...")
    rule_expander = RuleBasedExpansion(
        expansion_mm=args.expansion_mm,
        pixel_spacing_mm=args.spacing
    )
    ctv_mask = rule_expander.expand(gtv_mask)
    print(f"  规则外扩后 CTV 体素数: {ctv_mask.sum()}")

    # ---------- 边界保护：清理 CTV 中异常层 ----------
    cleaned_ctv = 0
    for z in range(ctv_mask.shape[2]):
        sl = ctv_mask[:, :, z]
        fg_ratio = sl.sum() / sl.size
        if fg_ratio > OUTPUT_RATIO:
            ctv_mask[:, :, z] = 0
            cleaned_ctv += 1
    if cleaned_ctv > 0:
        print(f"  清理 CTV 异常层: {cleaned_ctv} 层")

    # ---------- 学习型外扩（可选） ----------
    if args.ckpt_learning:
        ckpt_path = Path(args.ckpt_learning)
        if not ckpt_path.is_file():
            raise SystemExit(f"学习型权重不存在: {ckpt_path}")

        print(f"加载学习型外扩模型: {ckpt_path} ...")
        state = load_checkpoint(ckpt_path)
        model = LearningBasedExpansion(in_channels=1, out_channels=1)
        model.load_state_dict(state, strict=True)
        model = model.to(device).eval()

        print("逐层执行学习型外扩 ...")
        learned_ctv = np.zeros_like(gtv_mask, dtype=np.uint8)
        for z in range(gtv_mask.shape[2]):
            slice_gtv = gtv_mask[:, :, z]
            if slice_gtv.sum() == 0:
                continue
            t = torch.from_numpy(slice_gtv).float().unsqueeze(0).unsqueeze(0).to(device)
            with torch.no_grad():
                pred = model(t)
                pred = (pred > 0.5).float().squeeze().cpu().numpy()
            # 边界保护
            fg_ratio = pred.sum() / pred.size
            if fg_ratio > OUTPUT_RATIO:
                continue
            learned_ctv[:, :, z] = pred.astype(np.uint8)

        # 融合规则和学习型结果
        ctv_mask = np.logical_or(ctv_mask, learned_ctv).astype(np.uint8)
        print(f"  融合后 CTV 体素数: {ctv_mask.sum()}")

    # ---------- 保存 CTV ----------
    out_path = Path(args.out)
    if out_path.suffix.lower() != ".nrrd":
        out_path = out_path.with_suffix(".nrrd")
    nrrd.write(str(out_path), ctv_mask, header=gtv_header)
    print(f"已保存 CTV: {out_path}")

    # ---------- 统计 ----------
    expansion_ratio = ctv_mask.sum() / max(gtv_mask.sum(), 1)
    print(f"\n统计:")
    print(f"  GTV 体素: {gtv_mask.sum()}")
    print(f"  CTV 体素: {ctv_mask.sum()}")
    print(f"  外扩比例: {expansion_ratio:.2f}x")


if __name__ == "__main__":
    main()
