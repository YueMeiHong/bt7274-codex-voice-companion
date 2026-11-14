# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

[CmdletBinding()]
param(
    [switch]$Install,
    [switch]$DryRun,
    [string]$Python = 'py',
    [string]$TtsDirectory,
    [string]$AsrDirectory,
    [switch]$SkipDependencies,
    [ValidateSet('auto','cpu','cu128')][string]$TorchDevice='auto',
    [switch]$RequireModels,
    [switch]$SkipPluginRegistration
)
$ErrorActionPreference = 'Stop'
$levelRoot = [IO.Path]::GetFullPath($PSScriptRoot)
$helper = Join-Path $levelRoot 'scripts/runtime_paths.py'
$venvRoot = Join-Path $levelRoot '.venv-local'
$venvPython = Join-Path $venvRoot 'Scripts/python.exe'
$pluginRoot = Join-Path $levelRoot 'plugin/bt-companion'
$doInstall = $Install -and -not $DryRun

function Invoke-BtPython([string]$Executable, [string[]]$Arguments) {
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Python command failed (exit $LASTEXITCODE)." }
}

if (-not (Test-Path -LiteralPath $helper)) { throw 'Missing scripts/runtime_paths.py; use the complete BT-7274 package.' }
if ($TtsDirectory -and -not (Test-Path -LiteralPath $TtsDirectory -PathType Container)) { throw 'TtsDirectory does not exist.' }
if ($AsrDirectory -and -not (Test-Path -LiteralPath $AsrDirectory -PathType Container)) { throw 'AsrDirectory does not exist.' }
if (Test-Path -LiteralPath $venvRoot) {
    $venvItem=Get-Item -LiteralPath $venvRoot
    if ($venvItem.Attributes -band [IO.FileAttributes]::ReparsePoint) {
        throw '.venv-local is a junction/symlink. Refusing to modify a shared Python environment.'
    }
}

if (-not $doInstall) {
    Write-Host 'PRECHECK ONLY: no packages, models, manifests, or Codex state will be changed.'
    Write-Host "Independent environment: $venvRoot"
    Write-Host 'Model files are never downloaded automatically.'
    $existing = Join-Path $levelRoot '.venv/Scripts/python.exe'
    if (Test-Path -LiteralPath $venvPython) { $probe=$venvPython }
    elseif (Test-Path -LiteralPath $existing) { $probe=$existing }
    else { $probe=$Python }
    Invoke-BtPython $probe @($helper,'--root',$levelRoot,'--check','--no-modules')
    Write-Host 'Install with: .\Install-BT.ps1 -Install [-TtsDirectory <path>] [-AsrDirectory <path>]'
    return
}

if (-not (Test-Path -LiteralPath $venvPython)) {
    $bootstrapArgs=@()
    if ([IO.Path]::GetFileNameWithoutExtension($Python) -eq 'py') { $bootstrapArgs+=@('-3.12') }
    Invoke-BtPython $Python ($bootstrapArgs+@('-m','venv',$venvRoot))
}

$configurationArgs=@($helper,'--root',$levelRoot,'--configure','--python','.venv-local/Scripts/python.exe','--no-modules')
if ($TtsDirectory) { $configurationArgs+=@('--tts',[IO.Path]::GetFullPath($TtsDirectory)) }
if ($AsrDirectory) { $configurationArgs+=@('--asr',[IO.Path]::GetFullPath($AsrDirectory)) }
Invoke-BtPython $venvPython $configurationArgs

if (-not $SkipDependencies) {
    Invoke-BtPython $venvPython @('-m','pip','install','--upgrade','pip>=26.2','setuptools>=84.1.0')
    $btDevice=$TorchDevice
    if ($btDevice -eq 'auto') {
        $btDevice=if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {'cu128'} else {'cpu'}
    }
    $btTorchIndex=if ($btDevice -eq 'cu128') {'https://download.pytorch.org/whl/cu128'} else {'https://download.pytorch.org/whl/cpu'}
    Invoke-BtPython $venvPython @('-m','pip','install','torch==2.7.1','--index-url',$btTorchIndex)
    $requirements = Join-Path $levelRoot 'runtime/requirements-install.txt'
    New-Item -ItemType Directory -Path (Split-Path -Parent $requirements) -Force | Out-Null
    $lines = & $venvPython $helper --requirements
    if ($LASTEXITCODE -ne 0) { throw 'Could not build minimal dependency list.' }
    [IO.File]::WriteAllLines($requirements,[string[]]$lines,[Text.UTF8Encoding]::new($false))
    Invoke-BtPython $venvPython @('-m','pip','install','-r',$requirements)
}

$checkArgs=@($helper,'--root',$levelRoot,'--check','--strict')
if ($RequireModels) { $checkArgs+='--require-models' }
Invoke-BtPython $venvPython $checkArgs
if ($RequireModels) {
    Invoke-BtPython $venvPython @('-c','import sys;sys.path.insert(0,sys.argv[1]);from runtime_paths import tts_directory,asr_directory;from model_integrity import verify_model;verify_model("chinese_bt",tts_directory());verify_model("asr",asr_directory())',(Join-Path $levelRoot 'scripts'))
}

# Resolve paths on the installer's own machine. This also supports older Codex
# builds that leave PLUGIN_ROOT literal in stdio MCP arguments.
$mcp = & $venvPython $helper --root $levelRoot --mcp-config
if ($LASTEXITCODE -ne 0) { throw 'Could not generate local MCP launch configuration.' }
[IO.File]::WriteAllText((Join-Path $pluginRoot '.mcp.json'),($mcp -join "`n")+"`n",[Text.UTF8Encoding]::new($false))
$manifest = Get-Content -LiteralPath (Join-Path $pluginRoot '.codex-plugin/plugin.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$marketplaceName='bt-level25'
$marketplace=@{name=$marketplaceName;interface=@{displayName='BT-7274 Voice Companion'};plugins=@(@{
    name=$manifest.name;source=@{source='local';path='./plugin/bt-companion'};
    policy=@{installation='AVAILABLE';authentication='ON_INSTALL'};category='Productivity'
})}
$catalogDir=Join-Path $levelRoot '.agents/plugins'
New-Item -ItemType Directory -Path $catalogDir -Force | Out-Null
[IO.File]::WriteAllText((Join-Path $catalogDir 'marketplace.json'),($marketplace|ConvertTo-Json -Depth 12)+"`n",[Text.UTF8Encoding]::new($false))
if (-not $SkipPluginRegistration) {
    if (-not (Get-Command codex -ErrorAction SilentlyContinue)) { throw 'Codex CLI not found. Install it or retry with -SkipPluginRegistration.' }
    & codex plugin marketplace add $levelRoot
    if ($LASTEXITCODE -ne 0) { throw 'Codex could not register the local marketplace.' }
    & codex plugin add "$($manifest.name)@$marketplaceName"
    if ($LASTEXITCODE -ne 0) { throw 'Codex could not install the plugin.' }
}
Write-Host 'Installation finished. Codex was not restarted. API keys remain empty until configured by the user.'
