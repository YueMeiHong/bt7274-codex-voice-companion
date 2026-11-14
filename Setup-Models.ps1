# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

[CmdletBinding()]
param(
    [string]$ExistingTts,
    [string]$ExistingAsr,
    [switch]$Download,
    [switch]$DryRun,
    [string]$Python
)
$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath($PSScriptRoot)
$helper=Join-Path $root 'scripts/runtime_paths.py'
$assetRoot=Join-Path $root 'vendor-local'
$ttsRepo='https://www.modelscope.cn/studios/MiDd1Eye/BT7274-Bert-VITS2.git'
$ttsRevision='b4329163969de962a62ef05142efda40f9be9f26'
$asrRepo='csukuangfj/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17'
$asrRevision='2365baeacb507f821a0c8120fcee3d484dba7a07'
$ttsTarget=Join-Path $assetRoot 'BT7274-Bert-VITS2'
$asrTarget=Join-Path $assetRoot 'sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17'
$ttsRequired=@('models.py','configs/config.json','logs/bt/bt.pth','bert/chinese-roberta-wwm-ext-large/pytorch_model.bin')
$asrRequired=@('model.int8.onnx','tokens.txt')

function Assert-Assets([string]$Directory,[string[]]$Files) {
    foreach ($name in $Files) {
        $file=Join-Path $Directory $name
        if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Missing model asset: $file" }
        $stream=[IO.File]::OpenRead($file)
        try {
            $buffer=New-Object byte[] 128
            $count=$stream.Read($buffer,0,$buffer.Length)
            $header=[Text.Encoding]::ASCII.GetString($buffer,0,$count)
            if ($count -eq 0 -or $header.StartsWith('version https://git-lfs.github.com/spec/v1')) {
                throw "Asset is empty or only a Git LFS pointer: $file"
            }
        } finally { $stream.Dispose() }
    }
}

function Assert-OwnedDownloadTarget([string]$Path) {
    $absolute=[IO.Path]::GetFullPath($Path)
    if (-not $absolute.StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Download target must stay inside BT-7274.' }
    $check=$absolute
    while ($check -and $check.Length -ge $root.Length) {
        if (Test-Path -LiteralPath $check) {
            $item=Get-Item -LiteralPath $check -Force
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Refusing to download through a shared junction/symlink: $check" }
        }
        if ($check -eq $root) { break }
        $check=Split-Path -Parent $check
    }
}

function Invoke-ModelGit([string[]]$GitArgs) {
    & git @GitArgs
    if ($LASTEXITCODE -ne 0) { throw "Git model operation failed (exit $LASTEXITCODE)." }
}

function Save-SourceFile([string]$Url,[string]$Destination) {
    if (Test-Path -LiteralPath $Destination -PathType Leaf) {
        if ((Get-Item -LiteralPath $Destination).Length -gt 0) { return }
    }
    $partial=$Destination+'.partial'
    Write-Host "Downloading original source file: $([IO.Path]::GetFileName($Destination))"
    Invoke-WebRequest -Uri $Url -OutFile $partial -UseBasicParsing
    if ((Get-Item -LiteralPath $partial).Length -eq 0) { throw "Empty download: $Url" }
    Move-Item -LiteralPath $partial -Destination $Destination -Force
}

if ($ExistingTts) {
    $ttsTarget=[IO.Path]::GetFullPath($ExistingTts)
    Assert-Assets $ttsTarget $ttsRequired
}
if ($ExistingAsr) {
    $asrTarget=[IO.Path]::GetFullPath($ExistingAsr)
    Assert-Assets $asrTarget $asrRequired
}

Write-Host 'Model sources and exact revisions:'
Write-Host "  Chinese BT: $ttsRepo @ $ttsRevision"
Write-Host "  SenseVoice: https://huggingface.co/$asrRepo @ $asrRevision"
Write-Host "  BT directory: $ttsTarget"
Write-Host "  ASR directory: $asrTarget"
Write-Warning 'BT upstream README and LICENSE.txt disagree. This script records source files, but does not grant or certify redistribution rights. Resolve the model/voice licensing before a public release.'

if ($DryRun -or (-not $Download -and -not $ExistingTts -and -not $ExistingAsr)) {
    if (-not $ExistingTts) {
        Assert-OwnedDownloadTarget $ttsTarget
        Write-Host 'PLAN: git clone with GIT_LFS_SKIP_SMUDGE=1; checkout pinned BT revision.'
        Write-Host 'PLAN: git lfs pull only logs/bt/bt.pth and bert/chinese-roberta-wwm-ext-large/pytorch_model.bin.'
    }
    if (-not $ExistingAsr) {
        Assert-OwnedDownloadTarget $asrTarget
        Write-Host "PLAN: fetch model.int8.onnx, tokens.txt, LICENSE and README.md from https://huggingface.co/$asrRepo/resolve/$asrRevision/"
    }
    Write-Host 'PRECHECK ONLY: no models, configuration, or shared directories were changed.'
    return
}

if ($Download -and -not $ExistingTts) {
    Assert-OwnedDownloadTarget $ttsTarget
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'Git is required for the BT original source.' }
    Invoke-ModelGit @('lfs','version')
    New-Item -ItemType Directory -Path $assetRoot -Force | Out-Null
    $previousLfs=$env:GIT_LFS_SKIP_SMUDGE
    try {
        $env:GIT_LFS_SKIP_SMUDGE='1'
        if (-not (Test-Path -LiteralPath $ttsTarget)) {
            Invoke-ModelGit @('clone','--no-checkout',$ttsRepo,$ttsTarget)
        } elseif (-not (Test-Path -LiteralPath (Join-Path $ttsTarget '.git'))) {
            throw 'BT target already exists without Git metadata. Use -ExistingTts to register verified assets; refusing to overwrite it.'
        }
        $origin=(& git -C $ttsTarget remote get-url origin)
        if ($LASTEXITCODE -ne 0 -or $origin.TrimEnd('/') -ne $ttsRepo.TrimEnd('/')) { throw 'BT download target has an unexpected Git origin.' }
        Invoke-ModelGit @('-C',$ttsTarget,'checkout','--detach',$ttsRevision)
    } finally {
        if ($null -eq $previousLfs) { Remove-Item Env:GIT_LFS_SKIP_SMUDGE -ErrorAction SilentlyContinue }
        else { $env:GIT_LFS_SKIP_SMUDGE=$previousLfs }
    }
    Invoke-ModelGit @('-C',$ttsTarget,'lfs','pull','--include=logs/bt/bt.pth,bert/chinese-roberta-wwm-ext-large/pytorch_model.bin','--exclude=')
    Assert-Assets $ttsTarget $ttsRequired
}
if ($Download -and -not $ExistingAsr) {
    Assert-OwnedDownloadTarget $asrTarget
    New-Item -ItemType Directory -Path $asrTarget -Force | Out-Null
    foreach ($file in @('model.int8.onnx','tokens.txt','LICENSE','README.md')) {
        Save-SourceFile "https://huggingface.co/$asrRepo/resolve/$asrRevision/$file" (Join-Path $asrTarget $file)
    }
    Assert-Assets $asrTarget $asrRequired
}

if (-not $Python) {
    foreach ($candidate in @('.venv-local/Scripts/python.exe','.venv/Scripts/python.exe')) {
        $candidatePath=Join-Path $root $candidate
        if (Test-Path -LiteralPath $candidatePath) { $Python=$candidatePath;break }
    }
    if (-not $Python) { $Python='py' }
}
$configureArgs=@($helper,'--root',$root,'--configure','--no-modules')
if ($Download -or $ExistingTts) { $configureArgs+=@('--tts',$ttsTarget) }
if ($Download -or $ExistingAsr) { $configureArgs+=@('--asr',$asrTarget) }
& $Python @configureArgs
if ($LASTEXITCODE -ne 0) { throw 'Could not register model paths with runtime_paths.configure.' }

$sourceRecord=@{recordedOn=(Get-Date).ToString('o');tts=@{source=$ttsRepo;revision=$ttsRevision;directory=$ttsTarget;reused=[bool]$ExistingTts};asr=@{source="https://huggingface.co/$asrRepo";revision=$asrRevision;directory=$asrTarget;reused=[bool]$ExistingAsr};licenseStatus='BT source license metadata conflicts; redistribution rights not certified by setup.'}
$record=Join-Path $root 'config/model-sources.json'
[IO.File]::WriteAllText($record,($sourceRecord|ConvertTo-Json -Depth 6)+"`n",[Text.UTF8Encoding]::new($false))
Write-Host 'Model paths registered locally. Existing model directories were not modified.'
