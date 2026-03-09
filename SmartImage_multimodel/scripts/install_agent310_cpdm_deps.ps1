param(
    [string]$EnvName = "agent310"
)

$ErrorActionPreference = "Stop"

Write-Host "Installing CPDM dependencies into conda env: $EnvName"

$packages = @(
    "omegaconf>=2.3.0",
    "einops>=0.6.0",
    "pytorch-lightning>=1.9.0,<2.1.0",
    "segmentation-models-pytorch>=0.3.3,<0.4.0",
    "torchvision>=0.15.0",
    "tensorboard>=2.14.0"
)

conda run -n $EnvName python -m pip install @packages

Write-Host "Done."
