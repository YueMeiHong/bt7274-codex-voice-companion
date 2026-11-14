# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

[CmdletBinding(SupportsShouldProcess = $true)]
param([ValidateSet('bt-panel','bt-chat','bt-tts','bt-english')][string[]]$Services = @('bt-panel','bt-chat','bt-tts','bt-english'))

$ErrorActionPreference = 'Stop'
foreach ($name in $Services) {
    $scriptName = if ($name -eq 'bt-panel') { 'companion_service.py' } elseif ($name -eq 'bt-chat') { 'chat_service.py' } else { 'tts_service.py' }
    $scriptPath = Join-Path $PSScriptRoot "scripts\$scriptName"
    if ($name -eq 'bt-english') { $scriptPath=Join-Path $PSScriptRoot 'engines\gpt-sovits\upstream\api_v2.py' }
    # Windows venv python.exe is a redirector: the listener is a child Python.
    # Match this project's absolute script path, including orphaned children,
    # rather than stopping all Python processes or trusting a recycled PID.
    $allProcesses = @(Get-CimInstance Win32_Process)
    $targets = @($allProcesses | Where-Object {
        $_.Name -match '^pythonw?\.exe$' -and $_.CommandLine -and $_.CommandLine.IndexOf($scriptPath, [System.StringComparison]::OrdinalIgnoreCase) -ge 0
    })
    if ($targets.Count -eq 0) {
        Write-Host "$name is already stopped"
        continue
    }
    # Include only descendants of the verified project services (MCP stdio
    # servers and their launcher/console processes), never unrelated services.
    do {
        $targetIds = @($targets | ForEach-Object { $_.ProcessId })
        $children = @($allProcesses | Where-Object { $_.ParentProcessId -in $targetIds -and $_.ProcessId -notin $targetIds })
        $targets += $children
    } while ($children.Count -gt 0)
    $targetIds = @($targets | ForEach-Object { $_.ProcessId })
    $targets = $targets | Sort-Object @{ Expression = {
        $depth = 0
        $parentId = $_.ParentProcessId
        while ($parentId -in $targetIds -and $depth -lt 100) {
            $depth++
            $parentId = ($targets | Where-Object { $_.ProcessId -eq $parentId } | Select-Object -First 1).ParentProcessId
        }
        -$depth
    } }
    foreach ($target in $targets) {
        if ($PSCmdlet.ShouldProcess("$name PID $($target.ProcessId)", 'Stop project service')) {
            $live = Get-Process -Id $target.ProcessId -ErrorAction SilentlyContinue
            if ($live) {
                try { Stop-Process -Id $target.ProcessId -ErrorAction Stop }
                catch {
                    # A parent may exit as its stdio child closes.
                    if (Get-Process -Id $target.ProcessId -ErrorAction SilentlyContinue) { throw }
                }
                Wait-Process -Id $target.ProcessId -Timeout 10 -ErrorAction SilentlyContinue
            }
        }
    }
    if (-not $WhatIfPreference) { Write-Host "$name stopped" }
}
