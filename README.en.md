# BT-7274 Voice Companion for Codex

Project-authored code is licensed under AGPL-3.0-only. Third-party code and models retain their own notices; see THIRD_PARTY_NOTICES.md.

A Windows desktop plugin running on the user's own computer. Codex keeps its existing chats, models, permissions and execution tools. BT adds local speech recognition, reply playback and optional summaries. There is no developer-hosted service or cloud account for this plugin.

This is a preview for a future 1.0 release. Chinese voice works locally. English now uses DJMalachite's independently trained English BT Piper community model.

## Credits and community forks

I developed this free Titanfall 2 fan project with AI assistance. In the game, BT-7274 is voiced by Lin Yi-chi (林逸麒) in Mandarin and Glenn Steinbaum in English. The plugin synthesizes speech locally with the community models by [MiDd1Eye / Stardust_减 (Bert-VITS2)](https://www.modelscope.cn/studios/MiDd1Eye/BT7274-Bert-VITS2) and [DJMalachite (Piper)](https://github.com/DJMalachite/PiperVoiceModels). See the [credits and sources](README.md#配音模型与致谢).

This project is not endorsed by or affiliated with EA or its licensors.

I welcome free, open-source, ad-free forks for learning, education and community use. I discourage paid access, advertising and other monetization of this fan project. AGPLv3 governs the original code, including corresponding-source obligations for distributed modifications and modified versions that users interact with over a network. Third-party materials follow their own terms. I will review and correct confirmed copyright or attribution errors. Compatibility and translation updates depend on maintainer availability. Community fixes and translations are welcome. See [Support](SUPPORT.md).

## Install the complete source package

Use Windows, Python 3.12 and the Codex desktop app/CLI. Model downloading also needs Git and Git LFS. Keep the extracted package directory after installation: Codex launches the plugin from it.

```powershell
.\Setup-Models.ps1 -Download
.\Install-BT.ps1 -Install -RequireModels
```

Alternatively, supply existing model directories with `Setup-Models.ps1 -ExistingTts <BT-directory> -ExistingAsr <ASR-directory>`. See MODEL-SETUP.md for sources and the unresolved upstream voice-license questions. Models are downloaded from their original sources; they are not bundled in the source ZIP.

The installer creates `.venv-local` and does not change another project's Python environment. `-TorchDevice cpu` selects CPU PyTorch; NVIDIA machines default to CUDA 12.8. The current full runtime has been tested on Windows with an RTX 5090 D. Other hardware performance is not yet validated.

For English speech:

```powershell
.\Setup-English-BT.ps1
```

The English setup downloads the pretrained BT Piper model and its config (approximately 63 MB). It runs on the local CPU, needs no Chinese reference audio or cloud key, and opens no WebUI. See ENGLISH-VOICE.md.

## Native settings

Open Codex → Plugins → **BT-7274 Voice Companion** → Manage. Select **English** in Settings language. No browser or embedded web page is used.

Settings support Simplified Chinese, English and Japanese. Speech supports Chinese and English using separate local BT models. With summaries enabled, their language follows the speech selection, regardless of the settings language. Automatic speech selects Chinese/English from the original reply. Japanese is a settings language only, not a speech voice.

- Summary provider: DeepSeek, OpenAI, OpenAI-compatible or local Ollama. Each connection keeps its own URL, key and model. Use **Test current connection** after configuring it.
- Keys are ordinary local text in `config/providers.json`. No `.env` is read. This file is excluded from release archives and Git.
- Summaries are optional and off by default in a new installation. Cloud requests go directly from this computer to the chosen provider; local Ollama can use an empty key.
- Choose a conversation from the pinned/recent list, then enable BT. Only enabled conversations are monitored for new final replies. Original Codex replies are not modified.
- Defaults can be overridden per conversation. Volume uses a native numeric input, not a list of 101 values.
- Chinese and English previews play fixed local samples without reading chat content or calling the summary model.

## Native microphone

Microphone capture is off by default. Explicitly select and enable a chat, set its mode to **Voice conversation**, and enable the microphone. Auto-send is off by default: use **Read latest transcription**, review/edit the draft and click **Send draft to selected conversation**. With auto-send enabled, a pause ends the utterance and sends it to the selected chat.

Capture stops and pending audio is discarded when the target changes. **Stop recording and playback** does not stop Codex tasks. The physical microphone and desktop settings display still need human verification; synthetic-audio and mocked-device tests do not prove those work on every machine.

## Known host limits and verification

The current Codex native settings page does not provide verified live updates while it stays open. Opening the page or saving a setting fetches a fresh conversation list. **Read latest transcription** returns text through the native tool result; reopening settings refreshes the draft field. This is not advertised as automatic page refresh.

Tests cover local config persistence/provider isolation, native MCP settings, device/VAD behavior, draft routing, local synthesis/ASR and source packaging. Real cloud-provider tests require the user's own configuration. English intelligibility samples contain some ASR mismatches, and a successful WAV alone does not prove BT voice identity.

Run `Stop-BT.cmd` to stop this stage's backend, Chinese TTS and English engine. Local runtime logs/audio remain on this computer. Only a conversation title list is read for configuration; enabled reply playback reads final replies, and optional summarization sends those replies to the explicitly selected provider. No telemetry is implemented.

## Build

`Build-Release.ps1` creates and validates a source ZIP excluding user keys, conversations, `.env`, logs, recordings, environments and model weights. It has not been published to GitHub. A complete clone/extract → installer flow is supported; a bare marketplace entry without its runtime/dependencies is not claimed to be a complete installation.

For a Git marketplace installation, install bt-companion-level25@bt-level25 and ask Codex to complete BT setup with the bundled bt-setup skill. The entire source root is the plugin; do not copy only plugin/. First-run discovery does not download models or open a microphone.
