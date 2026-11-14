# Privacy / 隐私说明

BT runs on the user's Windows computer. There is no BT developer-hosted server,
telemetry, registration or developer account required for local speech.

- Microphone audio is captured only after the user enables it. Recognition and
  Chinese/English speech synthesis run locally using separately downloaded models.
- The plugin lists chat titles/IDs for selection. It reads final replies only for
  enabled chats; transcription is sent only to the explicitly selected chat under
  the selected draft/automatic-send settings. Codex and its model service retain
  their own data practices.
- Optional summaries send the final answer directly to the user's chosen model
  provider. They are off by default. API address, Key and model are saved in local
  configuration, never to a BT developer server. Provider policies apply to those
  requests. Local Ollama can be used without a cloud Key.
- Event logs do not persist chat/transcription text. Local drafts, settings and
  playback WAV files remain on the computer. The source package disables optional
  output-history recording by default; an existing user preference is preserved.
- Model/dependency setup connects to the listed upstream repositories, PyPI and
  PyTorch's package index. These services receive normal download requests.
- To remove data, first stop BT with Stop-BT.cmd, then delete this installation's
  local config files and runtime directory. For Git marketplace installs they are
  under `%LOCALAPPDATA%/BT-7274/Level25`; the plugin cache is a separate code copy. Remove the environment and downloaded
  model folders too if the full installation is no longer needed. Do not delete
  shared model directories supplied through -ExistingTts/-ExistingAsr.

本插件不向开发者上传 Key、聊天或录音。开启云摘要时，最终回答直接发送给用户
选择的供应商。麦克风、自动发送和云摘要均由用户显式配置。完整源码与第三方来源
随项目提供；报告安全问题的方法见 SECURITY.md。
