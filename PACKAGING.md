# BT-7274 源码运行包

这个包是本机运行的开发预览包，不是已发布的 1.0，也没有上传 GitHub。无需开发者服务器。选择云模型时，由使用者本机直接调用对应服务商；Ollama 可在本机完成摘要。

## 构建和验包

在完整的 BT-7274 源码目录执行：

```powershell
.\Build-Release.ps1
.\Build-Release.ps1 -VerifyOnly -ArchivePath "dist\实际生成的包名.zip"
```

产物位于 `dist/`，附带 SHA-256 与验包报告。构建使用文件白名单，不遍历模型或用户数据。每次保留独立源码 staging 目录，避免误删开发文件。

包含插件清单及服务器、运行脚本与测试、默认语音参数和发音词典、安装器、启动停止脚本、说明文档。包内的 MCP 路径是可移植占位符；安装器在目标机器生成自己的实际启动路径，不携带作者的电脑路径。

明确排除：真实 `providers.json`、`conversation-settings.json`、`runtime-paths.json`、英文引擎本机配置、`.env`、虚拟环境、运行日志、会话记录、录音、历史验收数据、模型权重、`vendor/`、`engines/` 和其他大文件下载。新用户初次读取配置时由程序产生空 Key 的默认连接；不会复制构建者的 Key 或订阅会话。

## 使用者安装

解压到自己选择的目录，先检查，再安装：

```powershell
.\Install-BT.ps1 -DryRun
.\Setup-Models.ps1 -Download
.\Install-BT.ps1 -Install -RequireModels
.\Setup-English-BT.ps1
```

已有模型也可显式指定：

```powershell
.\Install-BT.ps1 -Install -TtsDirectory "已准备的中文BT源码和模型目录" -AsrDirectory "已准备的SenseVoice模型目录"
```

安装器创建独立 `.venv-local` 并安装必要 Python 依赖，不修改其他项目环境。模型由上述独立准备脚本下载，或由使用者显式提供；不捆绑在源码包中。需要要求模型完整时加 `-RequireModels`。只准备源码环境时可省略模型参数；预检会明确列出缺少的文件，不能据此宣称语音已可用。

安装后在 Codex 原生 BT 插件设置中填写自己的服务商地址、API Key、模型。Key 保存在自己的本机配置，不需要开发者账户或服务器。

## 模型与平台边界

- 当前安装器面向 Windows。Python 3.12、Codex CLI、可用的音频输入/输出设备需要由目标机器提供。
- 中文 BT 需要完整 Bert-VITS2 源码、配置、BT 权重，以及中文 BERT 权重和 tokenizer 文件。
- ASR 需要 SenseVoice `model.int8.onnx` 和 `tokens.txt`。默认目录规则见 `scripts/runtime_paths.py`。
- 英文引擎是独立的可选安装，不包含在源码包中。只有完整安装并验收后才能声明英文声音可用；不要把摘要文本选项当作音色已支持。
- 作者原创代码采用 AGPLv3（AGPL-3.0-only）；第三方来源、具体使用部分与许可原文已整理在 THIRD_PARTY_NOTICES.md 和 third-party-licenses/。模型权重不随包分发；不把 GPL/AGPL 或声音权利改称 MIT。

## GitHub 分发范围

本阶段可以验证的是“完整源码仓库 clone 或完整 ZIP 解压 → Install-BT”。运行脚本位于完整包的 `scripts/`，发布版整个源码根目录包含 portable plugin.json / mcp.json、兼容清单、首次安装 skill 和后台脚本。marketplace 指向整个根目录；不再依赖宿主额外复制插件目录外的文件。首次需要按 bt-setup 安装依赖与模型，发现插件时不自动下载。仓库 marketplace 与官方公共目录是不同分发路线；本包没有执行发布或提交审核。
