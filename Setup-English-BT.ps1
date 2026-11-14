# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

[CmdletBinding()]
param([switch]$Start,[switch]$SkipInstall)
$ErrorActionPreference='Stop'
$root=$PSScriptRoot
$revision='179747d63a7355cce50833770f5bd6c41c213f3a'
$python=Join-Path $root '.venv-local/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $python)) {throw 'Run Install-BT.ps1 -Install first.'}
if (-not $SkipInstall) {
    & $python -m pip install 'piper-tts==1.8.0'
    if ($LASTEXITCODE) {throw 'Installing Piper failed.'}
    $modelRoot=Join-Path $root 'engines/piper-bt-english/PiperVoiceModels-main/Titanfall2/BT7274'
    New-Item -ItemType Directory -Path $modelRoot -Force | Out-Null
    $files=@{'BT7274.onnx'='aec69f5cb0b1bb3329a4f2294d2afc7c50149f82798e97d2cd9c8b450109adcf';'BT7274.onnx.json'='31d7694c5f6053b5794cb0ee2d50105790fd078442a43e62a30324c4631c4456'}
    foreach ($name in $files.Keys) {
        $path=Join-Path $modelRoot $name
        if (-not (Test-Path -LiteralPath $path)) {
            Invoke-WebRequest ('https://raw.githubusercontent.com/DJMalachite/PiperVoiceModels/'+$revision+'/Titanfall2/BT7274/'+$name) -OutFile ($path+'.download') -UseBasicParsing
            Move-Item -LiteralPath ($path+'.download') -Destination $path
        }
        $stream=[IO.File]::OpenRead($path);$hash=[Security.Cryptography.SHA256]::Create()
        try {$digest=([BitConverter]::ToString($hash.ComputeHash($stream))).Replace('-','').ToLowerInvariant()} finally {$stream.Dispose();$hash.Dispose()}
        if ($digest -ne $files[$name]) {throw "Model checksum mismatch: $name. Check the upstream model revision."}
    }
    $sourceRoot=Split-Path -Parent (Split-Path -Parent $modelRoot)
    foreach ($name in @('README.md','LICENSE')) {
        if (-not (Test-Path -LiteralPath (Join-Path $sourceRoot $name))) {
            Invoke-WebRequest ('https://raw.githubusercontent.com/DJMalachite/PiperVoiceModels/'+$revision+'/'+$name) -OutFile (Join-Path $sourceRoot $name) -UseBasicParsing
        }
    }
}
& $python -c "import sys;sys.path.insert(0,sys.argv[1]);import english_tts;from model_integrity import verify_model;verify_model('english_bt',english_tts.MODEL.parent);from piper import PiperVoice;PiperVoice.load(english_tts.MODEL,use_cuda=False);print('Pretrained English BT community voice ready on CPU. No background API is needed.')" (Join-Path $root 'scripts')
if ($LASTEXITCODE) {throw 'English BT model preflight failed.'}
