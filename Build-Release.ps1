# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

[CmdletBinding()]
param(
    [string]$OutputDirectory,
    [switch]$VerifyOnly,
    [string]$ArchivePath
)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
$root=[IO.Path]::GetFullPath($PSScriptRoot)
$utf8=[Text.UTF8Encoding]::new($false)
function Get-BtFileDigest([string]$Path) {
    $btStream=[IO.File]::OpenRead($Path);$btHash=[Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($btHash.ComputeHash($btStream))).Replace('-','').ToLowerInvariant() }
    finally {$btStream.Dispose();$btHash.Dispose()}
}

function Test-BtArchive([string]$Path) {
    $zip=[IO.Compression.ZipFile]::OpenRead($Path)
    try {
        $names=@()
        foreach ($entry in $zip.Entries) {
            $name=$entry.FullName.Replace('\','/');$names+=$name
            if ($name -match '(^|/)(\.env[^/]*|\.venv[^/]*|vendor|vendor-local|engines|runtime|downloads|acceptance|__pycache__)(/|$)' -or
                $name -match '(^|/)(providers|conversation-settings|runtime-paths|model-sources|english-tts|voice-state)\.json$' -or
                $name -match '\.(pth|onnx|safetensors|wav|mp3|log|pyc|sqlite|sqlite3)(\.|$)' -or
                $name -match '(^|/)\.\./' -or $name -match '^(/|[A-Za-z]:)') { throw "Forbidden release entry: $name" }
            if (@($names | Where-Object {$_ -ieq $name}).Count -gt 1) { throw "Duplicate release entry: $name" }
            if ($name -match '\.(py|ps1|cmd|md|json|txt|in|svg)$') {
                $reader=[IO.StreamReader]::new($entry.Open())
                try { $text=$reader.ReadToEnd() } finally { $reader.Dispose() }
                if ($text -match '\bsk-[A-Za-z0-9_-]{16,}' -or
                    $text -match '\b01[0-9a-f]{6}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b' -or
                    $text -match '(?i)[A-Z]:[\\/]Users[\\/]admin[\\/]') {
                    throw "Possible credential or personal-session data in: $name"
                }
            }
        }
        foreach ($required in @('Install-BT.ps1','Start-BT.ps1','Stop-BT.ps1','PACKAGING.md',
            'scripts/runtime_paths.py','scripts/provider_settings.py','plugin/bt-companion/server.py',
            'plugin/bt-companion/.mcp.json','.agents/plugins/marketplace.json','LICENSE',
            'THIRD_PARTY_NOTICES.md','config/model-integrity.json','requirements-runtime.in',
            'plugin.json','mcp.json','Launch-MCP.ps1','.codex-plugin/plugin.json',
            'skills/bt-setup/SKILL.md','.github/workflows/ci.yml','CONTRIBUTING.md','CHANGELOG.md')) {
            if ($required -notin $names) { throw "Missing release entry: $required" }
        }
        return @{passed=$true;entryCount=$names.Count;archive=[IO.Path]::GetFullPath($Path)}
    } finally { $zip.Dispose() }
}

if ($VerifyOnly) {
    if (-not $ArchivePath) { throw '-VerifyOnly requires -ArchivePath.' }
    Test-BtArchive ([IO.Path]::GetFullPath($ArchivePath)) | ConvertTo-Json -Compress
    return
}

if (-not $OutputDirectory) { $OutputDirectory=Join-Path $root 'dist' }
$output=[IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $output -Force | Out-Null
$stage=Join-Path $output ('source-stage-'+[Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $stage | Out-Null

# Explicit allowlist: never traverse a user's models, settings, or logs.
$files=@('Install-BT.ps1','Build-Release.ps1','Start-BT.ps1','Stop-BT.ps1',
    'Start-BT.cmd','Stop-BT.cmd','README.md','README.en.md','README.ja.md','PACKAGING.md','MODEL-SETUP.md','Setup-Models.ps1','ENGLISH-VOICE.md',
    'LICENSE','THIRD_PARTY_NOTICES.md','DISTRIBUTION.md','SECURITY.md','SECURITY-AUDIT.md','SECURITY-AUDIT-RESULTS.json',
    'dependency-inventory.json','requirements-runtime.in','requirements.lock.txt','.gitleaks.toml',
    'requirements-test.in','plugin.json','mcp.json','Launch-MCP.ps1','Install-Portable.ps1','.codex-plugin/plugin.json',
    'skills/bt-setup/SKILL.md','CONTRIBUTING.md','CHANGELOG.md','.editorconfig','.gitattributes',
    'LEGAL-REVIEW.md','LEGAL-STATUS.json','RIGHTS-REQUESTS.md','PRIVACY.md','SUPPORT.md','TERMS.md','PUBLIC-DIRECTORY-DRAFT.md','RELEASE-NOTES.md','Scan-Secrets.ps1',
    '.github/workflows/ci.yml','.github/workflows/release.yml','.github/dependabot.yml',
    'config/pronunciations.json','config/voice-profile.json','config/model-integrity.json',
    'plugin/bt-companion/server.py','plugin/bt-companion/.codex-plugin/plugin.json')
foreach ($optional in @('Setup-English-BT.ps1','Start-English-BT.ps1','Stop-English-BT.ps1')) {
    if (Test-Path -LiteralPath (Join-Path $root $optional)) { $files+=$optional }
}
$files+=@(Get-ChildItem -LiteralPath (Join-Path $root 'scripts') -File |
    Where-Object {$_.Extension -in @('.py','.ps1') -and $_.Name -notin @('english_crosslingual.py','english_engine_assets.py','test_english_crosslingual.py')} | ForEach-Object {'scripts/'+$_.Name})
$files+=@(Get-ChildItem -LiteralPath (Join-Path $root 'third-party-licenses') -File | ForEach-Object {'third-party-licenses/'+$_.Name})
$assets=Join-Path $root 'plugin/bt-companion/assets'
if (Test-Path -LiteralPath $assets) {
    $files+=@(Get-ChildItem -LiteralPath $assets -File |
        Where-Object {$_.Extension -in @('.svg','.png','.ico')} |
        ForEach-Object {'plugin/bt-companion/assets/'+$_.Name})
}

foreach ($name in ($files | Select-Object -Unique)) {
    $source=Join-Path $root $name
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Missing source file: $name" }
    $target=Join-Path $stage $name
    New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force | Out-Null
    Copy-Item -LiteralPath $source -Destination $target
}

# Preserve the author's local preference, but never ship enabled speech recording.
$profile=Get-Content -LiteralPath (Join-Path $stage 'config/voice-profile.json') -Raw | ConvertFrom-Json
$profile.save_recent_segments=$false
[IO.File]::WriteAllText((Join-Path $stage 'config/voice-profile.json'),($profile|ConvertTo-Json -Depth 8)+"`n",$utf8)

# Do not copy .mcp.json from this development machine. Install-BT resolves its
# own Python and server paths after extraction; placeholders are portable here.
$sourceMcp=Get-Content -LiteralPath (Join-Path $root 'plugin/bt-companion/.mcp.json') -Raw -Encoding UTF8 | ConvertFrom-Json
foreach ($property in $sourceMcp.mcpServers.PSObject.Properties) {
    $property.Value.command='python'
    $property.Value.args=@('${PLUGIN_ROOT}/server.py')
}
[IO.File]::WriteAllText((Join-Path $stage 'plugin/bt-companion/.mcp.json'),($sourceMcp|ConvertTo-Json -Depth 15)+"`n",$utf8)
[IO.File]::WriteAllText((Join-Path $stage 'plugin/bt-companion/bridge-config.json'),"{}`n",$utf8)
Copy-Item -LiteralPath (Join-Path $stage 'mcp.json') -Destination (Join-Path $stage '.mcp.json')
$manifest=Get-Content -LiteralPath (Join-Path $stage 'plugin/bt-companion/.codex-plugin/plugin.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$catalog=@{name='bt-level25';interface=@{displayName='BT Level 2.5'};plugins=@(@{
    name=$manifest.name;source=@{source='local';path='./'};
    policy=@{installation='AVAILABLE';authentication='ON_INSTALL'};category='Productivity'
})}
$catalogDirectory=Join-Path $stage '.agents/plugins'
New-Item -ItemType Directory -Path $catalogDirectory -Force | Out-Null
[IO.File]::WriteAllText((Join-Path $catalogDirectory 'marketplace.json'),($catalog|ConvertTo-Json -Depth 12)+"`n",$utf8)
[IO.File]::WriteAllText((Join-Path $stage '.gitignore'),".env*`n.venv*/`nvendor/`nvendor-local/`nengines/`nruntime/`ndist/`n__pycache__/`nconfig/providers.json`nconfig/companion-settings.json`nconfig/conversation-settings.json`nconfig/runtime-paths.json`nconfig/model-sources.json`nconfig/english-tts.json`n*.lock`n*.tmp`n*.log`n*.wav`n*.mp3`n",$utf8)

$archive=Join-Path $output ("BT-Level2.5-$($manifest.version)-source-preview-"+[DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss')+'.zip')
$inventory=@{version=$manifest.version;files=@(Get-ChildItem -LiteralPath $stage -Recurse -File -Force | ForEach-Object {
    @{path=$_.FullName.Substring($stage.Length+1).Replace('\','/');sha256=(Get-BtFileDigest $_.FullName)}
})}
[IO.File]::WriteAllText((Join-Path $stage 'package-files.json'),($inventory|ConvertTo-Json -Depth 8)+"`n",$utf8)
[IO.Compression.ZipFile]::CreateFromDirectory($stage,$archive,[IO.Compression.CompressionLevel]::Optimal,$false)
$report=Test-BtArchive $archive
$algorithm=[Security.Cryptography.SHA256]::Create()
$stream=[IO.File]::OpenRead($archive)
try { $report.sha256=([BitConverter]::ToString($algorithm.ComputeHash($stream))).Replace('-','').ToLowerInvariant() } finally { $stream.Dispose();$algorithm.Dispose() }
$report.rightsReviewStatus=(Get-Content -LiteralPath (Join-Path $stage 'LEGAL-STATUS.json') -Raw | ConvertFrom-Json).status
$report.bytes=(Get-Item -LiteralPath $archive).Length
$report.stage=$stage
$report.requirements='Python dependencies and model files are installed separately; no model weights are bundled.'
$receipt=$archive+'.verification.json'
[IO.File]::WriteAllText($receipt,($report|ConvertTo-Json -Depth 8)+"`n",$utf8)
$report | ConvertTo-Json -Depth 8
