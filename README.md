# BT-7274 语音伙伴｜Codex 插件

面向 Windows 的非官方 Codex 语音插件。支持本机麦克风转写、中英文 AI 语音播报和可选的回复摘要。

当前版本：**0.7.1**。作者原创代码采用 **AGPLv3（AGPL-3.0-only）**；第三方来源、使用部分和许可见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。安全修复见 [SECURITY-AUDIT.md](SECURITY-AUDIT.md)，分发路线见 [DISTRIBUTION.md](DISTRIBUTION.md)。

## 配音、模型与致谢

这个项目是我借助 AI 开发的《泰坦陨落 2》免费同人语音伙伴。感谢原作团队、配音演员和社区模型作者。

| 语言 | 游戏中 BT-7274 的配音 | 插件使用的 AI 语音模型 |
|---|---|---|
| 中文（国语） | [林逸麒（公开配音履历）](https://forum.gamer.com.tw/C.php?bsn=33645&snA=2202) | [MiDd1Eye（Stardust_减）／BT7274-Bert-VITS2](https://www.modelscope.cn/studios/MiDd1Eye/BT7274-Bert-VITS2)，使用 Bert-VITS2 AI 生成 |
| 英文 | [Glenn Steinbaum（游戏演职员表）](https://www.imdb.com/title/tt3612274/fullcredits/cast) | [DJMalachite／PiperVoiceModels](https://github.com/DJMalachite/PiperVoiceModels)，使用 Piper AI 生成 |

配音演员按原游戏角色致谢。插件播报由表中社区模型在本机合成。第三方许可和使用范围见 [第三方声明](THIRD_PARTY_NOTICES.md)。

This project is not endorsed by or affiliated with EA or its licensors.

## 二创与维护

欢迎 fork、改进、翻译和二创。原创插件代码使用 [AGPLv3](LICENSE)。分发修改版时，请保留版权与许可声明并按协议提供对应源码。若让用户通过网络与修改后的版本交互，也请按第 13 条向这些用户提供获取对应源码的方式。

我鼓励把二创免费、开源、无广告地分享，用于学习、教育和社区交流。我不鼓励把这个同人项目用于收费、插入广告或其他商业变现。这是创作倡议。原创代码的权利以 AGPLv3 为准，角色与社区语音按各自权利和上游条款处理。

如果你发现版权、署名或来源引用有误，欢迎通过项目的 Issues 或 [支持说明](SUPPORT.md) 告知我。我会核实并修正。兼容性和多语言更新视维护时间而定，欢迎社区提交修复和翻译。

## 现在已经实现

- 原生设置，支持简体中文、English 与日本語；没有设置网页或内嵌网页。
- DeepSeek、OpenAI、自定义 OpenAI 兼容、本机 Ollama；各自保存地址、Key 和模型，原生“测试当前连接”。
- Key 保存在自己的电脑 `config/providers.json`，默认全空；可在设置中按服务商填写。
- 置顶/最近会话选择、独立启用、用途、摘要和音量覆盖。音量为数字输入框；切换标题不会丢失按会话 ID 保存的配置。
- 原生麦克风开关、停顿分句、草稿编辑/发送、自动发送、停止收音和播报。默认不收音、不自动发送；切换目标会丢弃旧录音队列。
- 中文 BT 本机合成；DJMalachite 的独立英文 BT 社区 Piper 模型。固定试听按钮不读取聊天、不调用摘要模型。
- 独立 `.venv-local` 主环境；英文 Piper 直接在主环境运行；安装器、模型准备和源码打包脚本。

## 从哪里使用

Codex → 插件 → **BT-7274 Voice Companion** → 管理。

摘要服务参考 Cherry Studio / Open WebUI 的连接流程：先选服务商，再填地址、Key、模型，点击“测试当前连接”。字段失焦后由 Codex 自动保存。Ollama 本地通常不需要 Key。摘要默认关闭，新安装可以不用云 Key；开启后由本机直接请求用户选择的服务商，不改变 Codex 原回答。

设置界面语言与语音独立选择。语音选“中文”使用原有中文 BT，选“英文”使用独立英文 Piper BT；开启摘要时，摘要跟随语音语言。“自动（中英）”按原回复判断语言。没有独立的摘要文字语言选项。日语仅用于设置界面，当前不提供日语语音。

在会话列表选中原有或新会话，再启用 BT。新会话不会擅自自动开启。播报仅针对启用之后的新完成回复，不重播旧回答。

使用麦克风时，将选中会话用途设为“双向语音”，然后开启“本机麦克风”。关闭自动发送时，点击“读取最新转写”查看原生工具结果，再编辑草稿并发送。启用自动发送后，停顿结束即向该明确选中会话发送识别文字。停止按钮不停止 Codex 任务。

## 安装与模型

**完整源码安装**：解压源码包后，在包根目录运行下面的命令。源码包本身就是完整插件，不能只复制内部 `plugin/` 子目录。

**从 Codex marketplace 安装**：运行 `codex plugin marketplace add YueMeiHong/bt7274-codex-voice-companion`，然后在插件页安装 **BT-7274 Voice Companion**，然后让 Codex“帮我完成 BT 首次安装与配置”。内置 `bt-setup` 从插件实际目录运行 `Install-Portable.ps1 -Install`，把运行代码、依赖、模型和配置安装到 `%LOCALAPPDATA%/BT-7274/Level25`，避免插件缓存刷新丢失配置；首次未配置时只提供安装状态工具，不会在插件发现阶段自动下载或录音。安装后重新连接插件即可加载正式工具。

Windows、Python 3.12、Codex 桌面与 CLI。下载模型还需 Git、Git LFS。

```powershell
.\Setup-Models.ps1 -Download
.\Install-BT.ps1 -Install -RequireModels
```

已有模型可以用 `Setup-Models.ps1 -ExistingTts <BT目录> -ExistingAsr <ASR目录>` 登记。可以复用已有模型文件。详见 MODEL-SETUP.md。英文语音还需运行 `Setup-English-BT.ps1`。

安装器创建独立的 `.venv-local`。NVIDIA 默认使用 CUDA 12.8；`-TorchDevice cpu` 可选择 CPU。保留源码目录，插件从此目录运行；升级时保留 `config` 里的本机配置。安装器不重启 Codex。

英文安装：运行 `Setup-English-BT.ps1`，下载独立英文 BT 社区模型（约 63 MB）及配置，Piper 在本机 CPU 合成，不需要中文参考、云 Key 或额外的后台 API。来源及实测限制见 ENGLISH-VOICE.md。

当前实测硬件是 Windows + RTX 5090 D。其他硬件的速度不作保证。源码包不含模型、环境、录音、个人会话或 Key；全新机器下载安装仍需网络。安装好本地模型后，识别和中英文合成不需要云 TTS Key。

## 使用限制

- 当前 Codex 原生设置页没有已验证的实时刷新入口。打开或保存时重新读取列表；“读取最新转写”通过原生工具结果展示文字，重新打开设置可以刷新草稿字段。不把它称为已完成自动刷新。
- 麦克风已通过合成音频、模拟设备、路由与停止测试。
- 英文已实际生成有效 WAV，并做本地 ASR 可懂度检查；部分句子有词语偏差。英文播报仍为预览功能。
- 真实云模型连接需使用者在本版设置中填写自己的 Key。自动测试使用本机兼容服务。
- 第三方中文模型包含 AGPL 文本，英文 Piper 及模型包含 GPL/独立使用条款；来源与使用范围见 THIRD_PARTY_NOTICES.md。源码包不捆绑模型。

## 停止、打包和隐私

本目录 `Stop-BT.cmd` 停止语音插件后台服务。`Build-Release.ps1` 生成并验证完整源码 ZIP；支持完整解压/clone 后运行安装器。

列表配置只使用标题和 ID 等元数据。启用某会话播报后才读取该会话的最终回答；可选摘要会把该最终回答交给使用者选择的服务商。本机日志、草稿和音频不上传给开发者，也没有实现遥测。

其他语言：[English](README.en.md) · [日本語](README.ja.md)。

## 贡献与隐私

[贡献指南](CONTRIBUTING.md) · [版本记录](CHANGELOG.md) · [隐私说明](PRIVACY.md) · [使用帮助](SUPPORT.md)。发布仓库包含 Windows CI 和打包检查。
