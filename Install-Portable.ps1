# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors
[CmdletBinding()]
param([switch]$Install,[switch]$DryRun,[switch]$SkipEnglish,
      [ValidateSet('auto','cpu','cu128')][string]$TorchDevice='auto')
$ErrorActionPreference='Stop'
function Get-BtSha256([string]$Path) {
    $btStream=[IO.File]::OpenRead($Path);$btAlgorithm=[Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($btAlgorithm.ComputeHash($btStream))).Replace('-','').ToLowerInvariant() }
    finally {$btStream.Dispose();$btAlgorithm.Dispose()}
}
if (-not $env:LOCALAPPDATA) { throw 'Windows LOCALAPPDATA is required.' }
$btSource=[IO.Path]::GetFullPath($PSScriptRoot)
$btDestination=[IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'BT-7274/Level25'))
if (-not $btDestination.StartsWith([IO.Path]::GetFullPath($env:LOCALAPPDATA)+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Invalid BT installation destination.' }
if (-not $Install -or $DryRun) {
    @{mode='precheck';source=$btSource;destination=$btDestination;downloadsModels=$false;changesFiles=$false} | ConvertTo-Json -Compress
    return
}
$btInventory=Join-Path $btSource 'package-files.json'
if (-not (Test-Path -LiteralPath $btInventory)) { throw 'Use the complete built source package or Git marketplace package (package-files.json missing).' }
$btFiles=Get-Content -LiteralPath $btInventory -Raw -Encoding UTF8 | ConvertFrom-Json
# Validate all paths and hashes before copying anything. Package files never
# contain user Keys, drafts, runtime state, dependencies or models.
foreach ($btEntry in $btFiles.files) {
    $btRelative=$btEntry.path.Replace('/','\')
    $btFrom=[IO.Path]::GetFullPath((Join-Path $btSource $btRelative))
    $btTo=[IO.Path]::GetFullPath((Join-Path $btDestination $btRelative))
    if (-not $btFrom.StartsWith($btSource+'\',[StringComparison]::OrdinalIgnoreCase) -or
        -not $btTo.StartsWith($btDestination+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe package path.' }
    if ((Test-Path -LiteralPath $btTo) -and ((Get-Item -LiteralPath $btTo -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Refusing to overwrite a junction/symlink.' }
    if ((Get-BtSha256 $btFrom) -ne $btEntry.sha256) { throw "Package file changed: $($btEntry.path)" }
    $btWalk=Split-Path -Parent $btTo
    while ($btWalk -and $btWalk.Length -ge $btDestination.Length) {
        if ((Test-Path -LiteralPath $btWalk) -and ((Get-Item -LiteralPath $btWalk -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Refusing to install through a junction/symlink.' }
        if ($btWalk -eq $btDestination) { break };$btWalk=Split-Path -Parent $btWalk
    }
}
New-Item -ItemType Directory -Path $btDestination -Force | Out-Null
foreach ($btEntry in $btFiles.files) {
    $btTo=Join-Path $btDestination $btEntry.path
    if ($btSource -eq $btDestination) { continue }
    if ($btEntry.path -in @('config/voice-profile.json','config/pronunciations.json') -and (Test-Path -LiteralPath $btTo)) { continue }
    New-Item -ItemType Directory -Path (Split-Path -Parent $btTo) -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $btSource $btEntry.path) -Destination $btTo -Force
}
if ($btSource -ne $btDestination) { Copy-Item -LiteralPath $btInventory -Destination (Join-Path $btDestination 'package-files.json') -Force }
& (Join-Path $btDestination 'Setup-Models.ps1') -Download
& (Join-Path $btDestination 'Install-BT.ps1') -Install -RequireModels -SkipPluginRegistration -TorchDevice $TorchDevice
if (-not $SkipEnglish) { & (Join-Path $btDestination 'Setup-English-BT.ps1') }
Write-Host 'BT installed in a persistent local directory. Reconnect the plugin; no Codex restart was forced.'
