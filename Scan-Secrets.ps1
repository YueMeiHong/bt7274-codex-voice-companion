# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$Directory)
$ErrorActionPreference='Stop'
$btVersion='8.30.1'
$btExpectedSha='d29144deff3a68aa93ced33dddf84b7fdc26070add4aa0f4513094c8332afc4e'
$btCache=Join-Path ([IO.Path]::GetTempPath()) ('bt-gitleaks-'+$btVersion)
New-Item -ItemType Directory -Path $btCache -Force | Out-Null
$btZip=Join-Path $btCache 'gitleaks.zip'
if (-not (Test-Path -LiteralPath $btZip)) {
    Invoke-WebRequest -Uri "https://github.com/gitleaks/gitleaks/releases/download/v$btVersion/gitleaks_$($btVersion)_windows_x64.zip" -OutFile $btZip -UseBasicParsing
}
$btStream=[IO.File]::OpenRead($btZip);$btHash=[Security.Cryptography.SHA256]::Create()
try {$btActualSha=([BitConverter]::ToString($btHash.ComputeHash($btStream))).Replace('-','').ToLowerInvariant()}
finally {$btStream.Dispose();$btHash.Dispose()}
if ($btActualSha -ne $btExpectedSha) {
    throw 'Gitleaks download checksum mismatch; refusing execution.'
}
# Extract the verified binary again so an older writable cache cannot substitute it.
Expand-Archive -LiteralPath $btZip -DestinationPath $btCache -Force
$btReport=Join-Path $btCache ('scan-'+[Guid]::NewGuid().ToString('N')+'.json')
& (Join-Path $btCache 'gitleaks.exe') dir ([IO.Path]::GetFullPath($Directory)) --config (Join-Path $PSScriptRoot '.gitleaks.toml') --redact --no-banner --report-format json --report-path $btReport --log-level error
if ($LASTEXITCODE -ne 0) { throw "Secret scan failed; redacted report: $btReport" }
@{passed=$true;scanner="gitleaks $btVersion";report=$btReport} | ConvertTo-Json -Compress
