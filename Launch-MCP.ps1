# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors
$ErrorActionPreference='Stop'
$btRoot=$PSScriptRoot
$btPersistent=if ($env:LOCALAPPDATA) {Join-Path $env:LOCALAPPDATA 'BT-7274/Level25'} else {$null}
if (-not (Test-Path -LiteralPath (Join-Path $btRoot '.venv-local/Scripts/python.exe')) -and $btPersistent -and
    (Test-Path -LiteralPath (Join-Path $btPersistent 'plugin.json'))) {
    $btWanted=(Get-Content -LiteralPath (Join-Path $PSScriptRoot 'plugin.json') -Raw | ConvertFrom-Json).version
    $btInstalled=(Get-Content -LiteralPath (Join-Path $btPersistent 'plugin.json') -Raw | ConvertFrom-Json).version
    if ($btWanted -eq $btInstalled) { $btRoot=$btPersistent }
}
$btPython=Join-Path $btRoot '.venv-local/Scripts/python.exe'
if (Test-Path -LiteralPath $btPython) {
    & $btPython (Join-Path $btRoot 'scripts/runtime_paths.py') --root $btRoot --check --strict --require-models *> $null
    if ($LASTEXITCODE -eq 0) {
        & $btPython (Join-Path $btRoot 'plugin/bt-companion/server.py')
        exit $LASTEXITCODE
    }
}
# First install exposes a small, dependency-free status tool, not a broken
# speech service. No package/model downloads happen during MCP discovery.
if (Test-Path -LiteralPath $btPython) {
    & $btPython (Join-Path $PSScriptRoot 'scripts/bootstrap_mcp.py')
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3.12 (Join-Path $btRoot 'scripts/bootstrap_mcp.py')
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    & python (Join-Path $btRoot 'scripts/bootstrap_mcp.py')
} else {
    [Console]::Error.WriteLine('BT requires Python 3.12. Install Python, then run the packaged bt-setup skill.')
    exit 1
}
exit $LASTEXITCODE
