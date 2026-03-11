from __future__ import annotations

import importlib
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

REQUIRED_MODULES = [
    'yaml',
    'numpy',
    'PIL',
    'torch',
    'torchvision',
    'omegaconf',
    'einops',
    'pytorch_lightning',
    'segmentation_models_pytorch',
    'nrrd',
    'requests',
]


def main() -> int:
    ok = True
    print('[cpdm-check] importing required modules...')
    for name in REQUIRED_MODULES:
        try:
            importlib.import_module(name)
            print(f'  OK  {name}')
        except Exception as exc:
            ok = False
            print(f'  FAIL {name}: {exc}')

    print('[cpdm-check] resolving runtime paths...')
    try:
        from segmentation.cpdm_runner import _resolve_runtime  # pylint: disable=import-error

        runtime = _resolve_runtime(sample_step=None, device='cpu')
        checks = {
            'root_dir': Path(runtime.root_dir),
            'template_config': Path(runtime.template_config),
            'model_ckpt': Path(runtime.model_ckpt),
            'vqgan_ckpt': Path(runtime.vqgan_ckpt),
            'unet_ckpt': Path(runtime.unet_ckpt),
            'python_exe': Path(runtime.python_exe),
            'mplconfigdir': Path(runtime.mplconfigdir),
        }
        for title, path in checks.items():
            exists = path.exists()
            state = 'OK' if exists else 'FAIL'
            print(f'  {state:4} {title}: {path}')
            if not exists:
                ok = False
    except Exception as exc:
        ok = False
        print(f'  FAIL runtime resolve: {exc}')

    if ok:
        print('[cpdm-check] PASS')
        return 0
    print('[cpdm-check] FAIL')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
