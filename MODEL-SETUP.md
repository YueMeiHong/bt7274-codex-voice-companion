# 本机模型准备

脚本从模型作者的原始地址准备中文 BT TTS 和 SenseVoice。它不需要 Level 1，也不读取任何 `.env`。没有 `-Download` 时不会下载模型；`-DryRun` 始终只检查并显示计划。

## 已有模型：只登记，不复制、不修改

```powershell
.\Setup-Models.ps1 -ExistingTts 'C:\Models\BT7274-Bert-VITS2' -ExistingAsr 'C:\Models\SenseVoice' -DryRun
.\Setup-Models.ps1 -ExistingTts 'C:\Models\BT7274-Bert-VITS2' -ExistingAsr 'C:\Models\SenseVoice'
.\Install-BT.ps1 -Install -RequireModels
```

BT 目录须包含 `models.py`、`configs/config.json`、`logs/bt/bt.pth`、`bert/chinese-roberta-wwm-ext-large/pytorch_model.bin`。SenseVoice 目录须包含 `model.int8.onnx` 和 `tokens.txt`。脚本会拒绝空文件或尚未下载的 Git LFS 指针。

## 全新机器：明确选择下载

先安装 Python 3.12、Git、Git LFS，再运行：

```powershell
.\Setup-Models.ps1 -Download -DryRun
.\Setup-Models.ps1 -Download
.\Install-BT.ps1 -Install -RequireModels
```

模型下载到本阶段自己的 `vendor-local`，不使用可能指向旧项目的 `vendor` 目录。脚本拒绝经 junction/symlink 写入下载目录。BT 仓库保留原始代码、README 和许可证；只拉取所需的 PyTorch BT/BERT 权重，不下载同一 BERT 的 TensorFlow/Flax 版本。SenseVoice 保留原始 LICENSE、README。来源、版本和实际路径记录在 `config/model-sources.json`；运行路径通过现有 `runtime_paths.configure` 写入 `config/runtime-paths.json`。

可以混用已有与下载来源，例如 `-ExistingTts 'C:\Models\BT7274-Bert-VITS2' -Download` 只下载缺少的 ASR。

## 原始来源与固定版本

- 中文 BT：[MiDd1Eye / BT7274-Bert-VITS2](https://www.modelscope.cn/studios/MiDd1Eye/BT7274-Bert-VITS2)，Git `b4329163969de962a62ef05142efda40f9be9f26`。
- ASR：[csukuangfj / sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17](https://huggingface.co/csukuangfj/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17)，revision `2365baeacb507f821a0c8120fcee3d484dba7a07`。只需 int8 模型与词表，不下载完整 fp32 模型。

## 授权状态

BT 上游 README 的 Apache 标注与 `LICENSE.txt` 的 AGPL 文本存在冲突；游戏角色、训练素材和声音权利也不能由代码许可证代替。脚本保留来源，不自动接受或宣称许可清晰，不代表已经获准公开再分发模型。发布前须澄清授权。ASR 同样应保留其原始许可与作者来源。

已在本机实际从原始来源下载上述固定版本到新的 vendor-local 目录，并用独立 Python 环境启动中文 TTS 与 ASR。不是只有 DryRun，也没有依赖 Level 1 的模型联接。完全不同的干净 Windows 机器仍未实测；下载失败不会删除已有模型。
