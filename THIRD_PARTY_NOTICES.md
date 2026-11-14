# 第三方来源、使用范围与许可

核查日期：2026-11-09。项目作者原创的插件、会话适配、设置、路由、安装与安全检查代码使用 AGPLv3（AGPL-3.0-only），见 LICENSE。该许可不覆盖下载的第三方代码、模型权重、商标、角色或声音权利。项目源码包不包含模型、vendor、Python 环境或 npm bundle。

## 当前实际使用

| 来源 | 使用的部分和位置 | 上游许可与处理 |
| --- | --- | --- |
| [MiDd1Eye/BT7274-Bert-VITS2](https://www.modelscope.cn/studios/MiDd1Eye/BT7274-Bert-VITS2)，commit `b4329163969de962a62ef05142efda40f9be9f26` | `tts_service.py` 适配器调用其 `models.SynthesizerTrn`、`commons`、`utils.get_hparams_from_file`、`text.cleaner`、`text.get_bert`，使用 `configs/config.json`、`logs/bt/bt.pth` 和中文 BERT 权重；第三方代码由用户单独下载 | 实际 LICENSE.txt 为 **AGPL-3.0**，README 元数据写 Apache-2.0，不能称为 MIT。保留上游两份原文；源码包只提供适配器，不重许可上游。将适配器与该源码链接运行的组合须考虑 AGPL 条件，本项目原创贡献亦已采用 AGPLv3；上游原始声明继续保留。 |
| [DJMalachite/PiperVoiceModels](https://github.com/DJMalachite/PiperVoiceModels)，commit `179747d63a7355cce50833770f5bd6c41c213f3a` | 只下载 `Titanfall2/BT7274/BT7274.onnx` 和 `.onnx.json`，由 `english_tts.py` 调用；不复制 BT_TTS 项目代码 | LICENSE 为 GPL-3.0，README 同时声明 educational/personal use；保留两份原文，不宣称这些权重为 MIT。下载脚本固定 revision 并校验 SHA-256。 |
| [OHF-Voice/piper1-gpl](https://github.com/OHF-Voice/piper1-gpl)，`piper-tts==1.8.0` | 英文合成使用 `PiperVoice.load` 和 `synthesize_wav`；通过 pip 安装，不随包分发 | **GPL-3.0-or-later**，不是旧 rhasspy/piper 的 MIT 版本。保留运行库许可；项目 AGPLv3 声明不替代其 GPL 条件。 |
| [csukuangfj/SenseVoice ONNX](https://huggingface.co/csukuangfj/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17)，revision `2365baeacb507f821a0c8120fcee3d484dba7a07` | `companion_service.recognize` 使用 `model.int8.onnx` 和 `tokens.txt` 做本机语音识别 | 模型目录 LICENSE 指向 FunASR 许可页；FunASR 代码 MIT 与模型协议是不同文件。保留模型原 LICENSE；不把模型权重标成 MIT。[SenseVoice 原项目](https://github.com/FunAudioLLM/SenseVoice)、[FunASR LICENSE](https://github.com/modelscope/FunASR/blob/main/LICENSE)、[MODEL_LICENSE](https://github.com/modelscope/FunASR/blob/main/MODEL_LICENSE)。 |
| [k2-fsa/sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) | `OfflineRecognizer.from_sense_voice`、CPU 解码 API | Apache-2.0；运行库与模型许可分别保留。 |
| [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) | `server.py` MCP 服务、`native_codex.py` MCP 客户端、工具 schema | MIT；原始许可在 `third-party-licenses/mcp.txt`。 |
| [fastapi/fastapi](https://github.com/fastapi/fastapi) | 两个本机 HTTP 服务和请求校验 | MIT；保留 `third-party-licenses/fastapi.txt`。 |
| [spatialaudio/python-sounddevice](https://github.com/spatialaudio/python-sounddevice) | `native_microphone.py` 中的麦克风输入 | MIT；保留 `third-party-licenses/sounddevice.txt`。 |
| [Ailln/cn2an](https://github.com/Ailln/cn2an) | `speech_text.py` 中数字转中文读法 | MIT；保留 `third-party-licenses/cn2an.txt`。 |
| [fxsjy/jieba](https://github.com/fxsjy/jieba)、[mozillazg/python-pinyin](https://github.com/mozillazg/python-pinyin) | 中文模型的分词与拼音依赖，安装器安装 | MIT；分别保留原文。 |
| [tox-dev/filelock](https://github.com/tox-dev/filelock) | 设置文件和服务恢复互斥锁 | MIT；保留原文。 |
| PyTorch / Transformers / NumPy / SciPy / SoundFile / HTTPX / Uvicorn / librosa / typing-extensions | 张量推理、BERT、音频处理、HTTP、类型支持 | 分别含 BSD-3-Clause、Apache-2.0、ISC、PSF-2.0 等；实际安装版本与完整原文见 `dependency-inventory.json` 和 `third-party-licenses/`。 |
| [Unidecode](https://github.com/avian2/unidecode)，1.3.8 | 中文模型依赖安装项；不是本项目独立实现 | GPL-2.0-or-later；不是 MIT，保留原文。 |

第三方 MIT 来源继续保留其原版权与许可；BSD、Apache、GPL 等也分别保留原文。项目原创贡献采用 AGPLv3，并不把这些第三方文件全部改成 AGPLv3。GPLv3 与 AGPLv3 组合使用时遵守双方兼容条款。

## 未纳入当前发布包的历史内容

Open-LLM-VTuber / Web 曾用于 Level 1 原型；当前 Level 2.5 服务未导入其运行库或前端。`sources.json` 含早期路径与版本，不能用它代替当前依赖清单。GPT-SoVITS 跨语言实验不在当前默认工作流；相关脚本保留在开发目录，源码发布包排除这些未启用的历史实验。旧 HTML/JS 面板、npm bundle 和 Level 1/2 同样不随本次发布包分发。

## 名称与视觉素材

BT-7274 / Titanfall 相关名称、角色和声音不由本项目 AGPLv3 许可授予权利。图标是项目内 SVG 绘制的机器人插画，未发现内嵌位图、外部资源或游戏文件引用；它不是游戏版权授权证明。本项目是非官方社区项目。模型不捆绑、不上传，不声称取得游戏公司或配音演员的授权。


## 声音、语音识别、性格与通用接入方式

- 中文、英文声音是两个可识别的第三方模型来源；“模型权重”就是下载的 `.pth` / `.onnx` 等训练结果文件，不是额外的第三个性格项目。本次源码包不包含这些权重；保留的是来源、版权与许可说明。
- 麦克风转文字另外使用第三方 SenseVoice 模型及 sherpa-onnx 运行库。因此实际技术复用并不止两个声音。
- `config/bt-persona.md` 是开发目录中保存的角色提示词；当前 0.7.1 的运行脚本没有读取它，发布白名单也不包含它。当前摘要只使用 `companion_service.py` 内嵌的简短 BT 风格编辑指令。已回查“BT-7274复刻”原会话及 2026-11-07 调研报告，确认当时参考过 kuhaku9527/vl-interaction-dev（含 prompts/bt-7274.txt，仓库 LICENSE 为 Apache-2.0），还检索过 Ollama 的 theSage/bt-7274。原会话记录显示本地 bt-persona.md 是部署时新增并随后修改的文件；它与上游英文提示词的结构、内容和委派格式不同，当前没有直接复制或加载上游人格文件的记录。因此该项目列为调研参考，不把调研发现等同于实际代码/提示词复用。
- 多模型供应商接入由本项目 `provider_settings.py` / `provider_client.py` 实现：保存不同服务商的地址、Key、模型，通过 HTTPX 发送 OpenAI 兼容聊天请求。现有代码中没有导入或打包 Cherry Studio、Open WebUI 的供应商实现；README 提及它们是交互流程参考，不是已确认的代码复用。多供应商/兼容接口本身属于通用功能，若复制具体源码、提示词或素材，则另按该具体内容的许可处理。
- HTTPX、FastAPI、MCP SDK、PyTorch 等是基础运行依赖，与声音模型和角色灵感分开列出；使用这些库不等于整套插件来自它们。


## 原会话补查：BT 人格参考

- 参考项目：[kuhaku9527/vl-interaction-dev](https://github.com/kuhaku9527/vl-interaction-dev)。原始调研报告第 24 行及第 36–44 行讨论其 BT 人格、记忆和 Codex 桥接，并建议参考部分设计，没有记录整套采用。
- 上游人格文件：[prompts/bt-7274.txt](https://github.com/kuhaku9527/vl-interaction-dev/blob/main/prompts/bt-7274.txt)，包含英文 Identity、Core Protocols、Behavior Model、Delegation Protocol 等段落，使用 `</delegation>` 委派标记。
- 上游许可：[LICENSE](https://github.com/kuhaku9527/vl-interaction-dev/blob/main/LICENSE)，核查时为 Apache-2.0。
- 本地中文人格文件强调日常语音、克制幽默、工具事实边界等，没有上游的 Hermes 身份、P1/P2/P3 结构或委派标记。0.7.1 运行时采用的是内嵌摘要编辑指令，未加载该完整人格文件，也未打包上述第三方文件。
- 另一条调研线索是 [theSage/bt-7274](https://ollama.com/theSage/bt-7274)；未发现下载或加载该 Ollama 角色的记录。保留为调研线索，不列作实际运行依赖。
