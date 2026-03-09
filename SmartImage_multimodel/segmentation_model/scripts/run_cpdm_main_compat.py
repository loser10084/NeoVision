from __future__ import annotations

import argparse
import inspect
import os
import runpy
import sys
from pathlib import Path

import torch


def _patch_reduce_on_plateau() -> None:
    cls = torch.optim.lr_scheduler.ReduceLROnPlateau
    sig = inspect.signature(cls.__init__)
    if "verbose" in sig.parameters:
        return

    class _CompatReduceLROnPlateau(cls):
        def __init__(
            self,
            optimizer,
            mode: str = "min",
            factor: float = 0.1,
            patience: int = 10,
            threshold: float = 1e-4,
            threshold_mode: str = "rel",
            cooldown: int = 0,
            min_lr=0,
            eps: float = 1e-8,
            verbose: bool = False,
        ):
            super().__init__(
                optimizer=optimizer,
                mode=mode,
                factor=factor,
                patience=patience,
                threshold=threshold,
                threshold_mode=threshold_mode,
                cooldown=cooldown,
                min_lr=min_lr,
                eps=eps,
            )

    torch.optim.lr_scheduler.ReduceLROnPlateau = _CompatReduceLROnPlateau


def main() -> None:
    parser = argparse.ArgumentParser(description="Run CPDM main.py with torch compatibility patches")
    parser.add_argument("--cpdm_root", required=True, help="Path to CPDM-main root")
    args, rest = parser.parse_known_args()

    cpdm_root = Path(args.cpdm_root).resolve()
    main_script = cpdm_root / "main.py"
    if not main_script.is_file():
        raise FileNotFoundError(f"CPDM main.py not found: {main_script}")

    _patch_reduce_on_plateau()

    os.environ.setdefault("TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD", "1")

    if rest and rest[0] == "--":
        rest = rest[1:]

    sys.path.insert(0, str(cpdm_root))
    sys.argv = [str(main_script)] + rest
    runpy.run_path(str(main_script), run_name="__main__")


if __name__ == "__main__":
    main()
