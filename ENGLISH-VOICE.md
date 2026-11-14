# 英文 BT：独立社区模型

默认英文路径已纠正为 DJMalachite 发布的预训练 Piper BT-7274 模型，语言配置为 `en`。它与中文 BT Bert-VITS2 是两套独立权重，不使用中文参考音频，不做中文音色跨语言转换。

- 原作者与模型：https://github.com/DJMalachite/PiperVoiceModels
- 原作者发布帖：https://www.reddit.com/r/titanfall/comments/1kd79x6/update_bt7274_voice_model_now_public/
- 复用该模型的台词项目：https://github.com/rmac-silva/BT_TTS

作者说明模型使用定制音频片段模仿 BT，有限数据会造成部分词发音不准。已有发布、演示及复用证据，但没有足够依据称为社区公认最佳或最热门。也不把作者的“模仿 BT”描述升级成已经确认原版游戏录音训练。

## 安装和运行

主环境准备后执行 `Setup-English-BT.ps1`，安装固定版本 Piper 并从原作者地址获取约 63 MB ONNX 权重和 JSON 配置，校验 SHA-256，保留 README 与 LICENSE。所有合成在本机 CPU 完成，没有云 Key、中文参考或额外 HTTP 后台。

设置中的“自动（中英）”或“英文 BT（实验）”现在使用该模型。英文仍保留实验标记，因为相似度需要人耳验收。原生“试听英文 BT”使用这一独立模型。

实测样例 `acceptance/english-bt-piper.wav` 为 22.05 kHz、单声道，约 4.79 秒。本地 ASR 正确识别样例句，不能据此代替音色判断。

## 旧实验

GPT-SoVITS 中文参考跨语言方案保留在 `english_crosslingual.py`、`Setup-English-Crosslingual.ps1` 和 engines/gpt-sovits 中作为历史实验；已停止旧服务，不作为默认英文实现。下载的大文件不会打入发布源码包，也没有自动删除用户工作文件。

## 来源与分发

源仓库同时存在 GPL-3.0 LICENSE 与 README 的个人/教育用途描述。公开分发模型和角色素材前仍需核对相应权利；源码包不包含这些模型权重。没有宣称取得原游戏角色或演员声音的授权。
