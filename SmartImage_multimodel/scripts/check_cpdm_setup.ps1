param(
    [string]$EnvName = 'agent310'
)

$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$pythonExe = "D:/tools/Miniconda/envs/$EnvName/python.exe"
if (Test-Path $pythonExe) {
    & $pythonExe "$scriptDir\check_cpdm_setup.py"
    exit $LASTEXITCODE
}

$condaExe = $null
try {
    $condaExe = (Get-Command conda -ErrorAction Stop).Source
} catch {
    if (Test-Path 'D:/tools/Miniconda/Scripts/conda.exe') {
        $condaExe = 'D:/tools/Miniconda/Scripts/conda.exe'
    }
}

if (-not $condaExe) {
    throw "conda not found and python exe for env '$EnvName' does not exist."
}

& $condaExe run -n $EnvName python "$scriptDir\check_cpdm_setup.py"
exit $LASTEXITCODE