from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pytorch_lightning as pl
import segmentation_models_pytorch as smp
import torch


class SegmentationModel(pl.LightningModule):
    """Inference-only wrapper for loading the CPDM attention UNet checkpoint."""

    def __init__(
        self,
        arch: str,
        encoder_name: str,
        in_channels: int,
        out_classes: int,
        encoder_weights: str | None = None,
        **kwargs,
    ):
        super().__init__()
        self.model = smp.create_model(
            arch,
            encoder_name=encoder_name,
            in_channels=in_channels,
            classes=out_classes,
            encoder_weights=encoder_weights,
            **kwargs,
        )

        # Keep checkpoint compatibility with original CPDM segmentation module.
        params = smp.encoders.get_preprocessing_params(encoder_name)
        self.register_buffer("std", torch.tensor(params["std"]).view(1, 3, 1, 1))
        self.register_buffer("mean", torch.tensor(params["mean"]).view(1, 3, 1, 1))

    def forward(self, image: torch.Tensor) -> torch.Tensor:
        return self.model(image)


def _load_ct_npy(path: Path) -> np.ndarray:
    arr = np.asarray(np.load(str(path), allow_pickle=True), dtype=np.float32).squeeze()
    if arr.ndim != 2:
        raise ValueError(f"CT input must be 2D after squeeze, got shape={arr.shape}")
    arr = np.clip(arr, 0.0, 2047.0) / 2047.0
    return arr.astype(np.float32, copy=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate CPDM attention map for one CT slice (.npy).")
    parser.add_argument("--ct_npy", required=True, help="Path to input CT .npy (2D, preprocessed to 256x256).")
    parser.add_argument("--ckpt", required=True, help="Path to UNET_AttentionMap_step_9000.ckpt.")
    parser.add_argument("--out_npy", required=True, help="Path to output attention map .npy.")
    parser.add_argument("--arch", default="Unet", help="Segmentation architecture name.")
    parser.add_argument("--encoder_name", default="resnet50", help="Encoder name.")
    parser.add_argument("--device", default="", help="cuda / cpu. Empty means auto.")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if args.device:
        device = torch.device(args.device)

    model = SegmentationModel.load_from_checkpoint(
        str(Path(args.ckpt)),
        arch=args.arch,
        encoder_name=args.encoder_name,
        in_channels=1,
        out_classes=1,
        encoder_weights=None,
        map_location=device,
    )
    model = model.to(device).eval()

    ct = _load_ct_npy(Path(args.ct_npy))
    x = torch.from_numpy(ct).unsqueeze(0).unsqueeze(0).to(device)
    with torch.no_grad():
        logits = model(x)
        prob = torch.sigmoid(logits)[0, 0].detach().cpu().numpy().astype(np.float32)

    out_path = Path(args.out_npy)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(str(out_path), prob)


if __name__ == "__main__":
    main()

