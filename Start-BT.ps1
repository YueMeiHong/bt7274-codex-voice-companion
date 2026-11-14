# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$btIndependent = Join-Path $projectRoot '.venv-local\Scripts\python.exe'
if (Test-Path -LiteralPath $btIndependent) { $python=$btIndependent }
$btRuntimeConfiguration=Join-Path $projectRoot 'config/runtime-paths.json'
if (Test-Path -LiteralPath $btRuntimeConfiguration) {
    $btPaths=Get-Content -LiteralPath $btRuntimeConfiguration -Raw | ConvertFrom-Json
    if ($btPaths.python) {
        $python=if ([IO.Path]::IsPathRooted($btPaths.python)) {$btPaths.python} else {Join-Path $projectRoot $btPaths.python}
    }
}
if (-not (Test-Path -LiteralPath $python)) { throw 'Run Install-BT.ps1 -Install to prepare this computer.' }
$runtime = Join-Path $projectRoot 'runtime'
New-Item -ItemType Directory -Path $runtime -Force | Out-Null

function Start-BtService($name, $script, $port, $healthPath) {
    $url = "http://127.0.0.1:$port/$healthPath"
    $health = $null
    try { $health = Invoke-RestMethod $url -TimeoutSec 2 } catch {}
    if ($health.ready) {
        if ($name -eq 'bt-chat' -and $health.llm -ne 'Codex app-server') { throw 'Another BT version is running. Stop it before switching Level.' }
        return
    }
    if (Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue) {
        throw "Port $port is occupied by a different or unready service."
    }
    $stdout = Join-Path $runtime "$name.stdout.log"
    $stderr = Join-Path $runtime "$name.stderr.log"
    $process = Start-Process -FilePath $python -ArgumentList ('"' + (Join-Path $projectRoot $script) + '"') -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    $process.Id | Set-Content (Join-Path $runtime "$name.pid")
    $deadline = (Get-Date).AddSeconds(180)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 1
        if ($process.HasExited) { throw "$name exited; inspect runtime/$name.stderr.log" }
        $health = $null
    try { $health = Invoke-RestMethod $url -TimeoutSec 2 } catch {}
    if ($health.ready) {
        if ($name -eq 'bt-chat' -and $health.llm -ne 'Codex app-server') { throw 'Another BT version is running. Stop it before switching Level.' }
        return
    }
    }
    throw "$name startup timed out; inspect runtime/$name.stderr.log"
}

Start-BtService 'bt-tts' 'scripts\tts_service.py' 12397 'health'
Start-BtService 'bt-panel' 'scripts\companion_service.py' 12396 'health'
Write-Host 'BT-7274 backend ready. Settings: Codex > Plugins > BT-7274 > Manage.'
if ($env:BT_OPEN_DEBUG_PANEL -eq '1') {
    $chrome = Join-Path $env:ProgramFiles 'Google\Chrome\Application\chrome.exe'
    if (Test-Path -LiteralPath $chrome) {
        Start-Process -FilePath $chrome -ArgumentList '--app=http://127.0.0.1:12396'
    } else {
        Start-Process 'http://127.0.0.1:12396'
    }
}
