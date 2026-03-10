param(
    [switch]$AlsoClearUserCache
)

$ErrorActionPreference = 'SilentlyContinue'
$frontendRoot = Split-Path -Parent $PSScriptRoot
Write-Host "Frontend root: $frontendRoot"

$localTargets = @(
    (Join-Path $frontendRoot 'unpackage'),
    (Join-Path $frontendRoot '.hbuilderx')
)

foreach ($target in $localTargets) {
    if (Test-Path $target) {
        Remove-Item -Recurse -Force $target
        Write-Host "Removed: $target"
    }
}

if ($AlsoClearUserCache) {
    $userTargets = @(
        (Join-Path $env:LOCALAPPDATA 'HBuilderX\Cache'),
        (Join-Path $env:LOCALAPPDATA 'HBuilderX\projects')
    )
    foreach ($target in $userTargets) {
        if (Test-Path $target) {
            Remove-Item -Recurse -Force $target
            Write-Host "Removed user cache: $target"
        }
    }
}

Write-Host 'Done. Reopen HBuilderX and rebuild Android package.'