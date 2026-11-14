# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

$ErrorActionPreference = 'Stop'
$levelRoot = Split-Path -Parent $PSScriptRoot
$launcher = Join-Path $levelRoot 'Start-BT.ps1'
# MCP closes its Windows job at disconnect. Ask Windows to own the explicitly
# requested background services rather than making them children of that job.
# No credentials are written to disk and no security settings are changed.
$allowed = @('SystemRoot','WINDIR','ComSpec','PATH','PATHEXT','TEMP','TMP','USERPROFILE','USERNAME','USERDOMAIN','LOGNAME','HOMEDRIVE','HOMEPATH','LOCALAPPDATA','APPDATA','PROGRAMFILES','PROGRAMFILES(X86)','CODEX_THREAD_ID','CODEX_SESSION_ID','CODEX_APP_TOOLS_PIPE_PATH','CODEX_MCP_NODE_PATH','CODEX_BROWSER_USE_NODE_PATH','CODEX_ELECTRON_RESOURCES_PATH','CODEX_CLI_PATH')
$childEnvironment = @(Get-ChildItem Env: | Where-Object { $_.Name -in $allowed } | ForEach-Object { "$($_.Name)=$($_.Value)" })
$childEnvironment += 'BT_NO_BROWSER=1'
$startup = New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{ ShowWindow = [uint16]0; EnvironmentVariables = [string[]]$childEnvironment }
$command = 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "' + $launcher + '"'
$result = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = $command; CurrentDirectory = $levelRoot; ProcessStartupInformation = $startup }
if ($result.ReturnValue -ne 0) { throw "Windows could not start the BT service: $($result.ReturnValue)" }
@{ processId = $result.ProcessId } | ConvertTo-Json -Compress
