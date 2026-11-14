# 发布权利核查 — 2026-11-14

当前发行方案是免费、无广告的同人源码，安装器从上游下载模型。以下记录保留 EA 政策及上游权利的适用疑点。发布决定由项目作者作出，Codex 官方目录另有独立审核流程。早期报告中的自动发布门槛已移除。

## 具体资产、结论与处理

| 范围 | 已核对事实 | 当前处理与解除条件 |
|---|---|---|
| 原创适配器、安装器、设置与服务代码 | 已采用 AGPL-3.0-only，保留完整许可证、源码及第三方许可目录 | 继续保留；AGPL 不对第三方角色、商标、录音、声音人格权授予许可 |
| 中文 BT 模型 | MiDd1Eye/BT7274-Bert-VITS2，固定提交 b4329163969de962a62ef05142efda40f9be9f26；LICENSE.txt 是 AGPLv3，而 README 元数据写 Apache-2.0；app.py 要求署名、项目链接及 Bert-VITS2 AI 生成说明 | 已补署名与 AI 提示；需作者澄清各文件/权重许可，并提供训练音频、表演与声音合成授权依据。未找到授权记录不等于已经证明未经授权 |
| 英文 BT 模型 | DJMalachite/PiperVoiceModels，固定提交 179747d63a7355cce50833770f5bd6c41c213f3a；仓库 GPLv3，但 README 写教育/个人用途，并说明模仿 Titanfall 2 的 BT | 需澄清权重许可范围与声音/录音授权链。不能据 GPL 推定演员声音许可，也不能将 README 限制偷偷并入本项目 AGPL |
| BT 名称、角色、性格表现及机器人图标 | 来源指向 Titanfall 的 BT-7274；图标虽自行绘制，仍需核对角色形象衍生使用。未打包官方截图不等于角色使用已清权 | 已添加非官方声明；EA 同人政策不是独立插件及声音克隆的全面许可。保留核心 BT 身份时，需确认该具体用途的授权范围 |
| 性格参考 | 调研曾参考 kuhaku9527/vl-interaction-dev；当前运行包使用本项目短提示词，不读取完整第三方 persona 文件 | 保留第三方来源说明；通用多供应商 API 接口思路本身不等于复制某家代码，实际依赖仍按清单署名 |
| ASR、BERT、运行库 | 使用 SenseVoice ONNX、hfl/chinese-roberta-wwm-ext-large 及依赖清单中的软件，实际复用不止两种声音；代码许可与模型许可分别记录 | 保留 THIRD_PARTY_NOTICES.md、dependency-inventory.json、third-party-licenses/ 与固定来源。BERT 模型卡标注 Apache-2.0；不把 SenseVoice 权重推定为 MIT |
| Codex / OpenAI 标识 | 仅说明兼容用途，不使用 OpenAI 标志或声称官方认证 | 建议仓库名 bt7274-codex-voice-companion，展示名 BT-7274 Voice Companion for Codex；这是命名建议，不是商标授权结论 |
| 录音、个人信息、摘要供应商 | 本地服务、有鉴权、默认发行配置不保存语音片段；可选云摘要会向用户所选服务发送内容 | 保留 PRIVACY.md 的实际数据流说明；不发布本机配置、密钥、会话、录音或历史材料。未引入开发者云端或收费服务 |
| AI 合成标识与服务规则 | 本地软件分发与面向公众提供在线生成服务不能混为一谈；中国相关规则有各自适用范围 | 设置界面与文档已加 AI 合成说明。公开演示须同时标明 AI 合成；未来若上线公共推理服务，须另核服务适用义务，不沿用本地版本结论 |

## 权威依据及适用边界

英文仓库的提交顺序是 [初始提交加入 GPLv3](https://github.com/DJMalachite/PiperVoiceModels/commit/4e383bdae17ecdd3cb2e553340233a3031753288)、[上传 BT 模型](https://github.com/DJMalachite/PiperVoiceModels/commit/0ad03f5876b006f25137002c56230d103d329954)、[README 加入教育与个人用途说明](https://github.com/DJMalachite/PiperVoiceModels/commit/fc74f42675b9edb575e6166aea2f1defd4628d00)。权重首次发布时已在有 GPLv3 文件的仓库内，这支持按 GPLv3 理解作者授予的版权许可。随后出现的 README 说明使权重的许可范围仍有解释空间。当前源码包不附带权重，安装器直接从原仓库下载，应与由本项目托管或再分发权重分别评估。

这次复核以安装器指定的版本为准。中文版检查了安装目录的 README.md、LICENSE.txt、app.py 与 logs/bt/bt.pth。作者要求二创署名，表明其预期有人发布二创作品。该说明没有明确指定权重适用哪份协议。英文版直接读取了固定提交的 LICENSE、README.md 和模型配置。README 说训练使用定制音频来模仿 BT，未交代是作者自录、第三方录制还是源自游戏。两套材料均未提供独立的权重许可说明。若已明确适用的开源许可证覆盖具体资产和用途，遵守条款即可使用作者有权授出的部分，无须另外索取同样的许可。

EA 明确允许附条件的个人同人项目，包括同人网站和视频。免费发布满足不出售作品这一点。政策仅对部分被动广告和视频变现列出例外，且另有限制衍生产品及与第三方产品、服务或品牌结合的条款。政策允许使用原创角色，同时明确排除 EA 从第三方取得的受限制内容，声音和表演是它列举的例子。角色能有标志性的声音，具体录音、表演和可识别真人的声音仍要看来源。这里没有证据认定任一模型实际使用了游戏录音或克隆了特定演员。

- [EA 内容政策](https://help.ea.com/en/articles/security-and-rules/ea-content-policy/)：同人使用附条件，限制商业使用、混淆官方关系等；明确不授予第三方内容（包括声音/表演）的许可。免费、开源、不捆绑权重均不能单独补上缺失权利。
- [英文模型原仓库](https://github.com/DJMalachite/PiperVoiceModels)、[中文模型原项目](https://www.modelscope.cn/studios/MiDd1Eye/BT7274-Bert-VITS2)：核对的是当前引用资产的原始声明，不以其他人的发布行为作为许可证明。
- [民法典](https://www.cac.gov.cn/2020-06/01/c_15925617772683193.htm)第 1023 条：自然人声音保护参照肖像权。是否能识别具体自然人需要事实判断；拥有录音版权不自动拥有声音克隆同意。
- [OpenAI 品牌指南](https://openai.com/brand/)及[插件指南](https://developers.openai.com/plugins/plugin-guidelines)：不暗示官方背书，使用内容须有相应权利。
- [生成式人工智能服务管理暂行办法](https://www.cac.gov.cn/2023-07/13/c_1690898327029107.htm)、[人工智能生成合成内容标识办法](https://www.cac.gov.cn/2025-03/14/c_1743654684782215.htm)：按实际提供的服务及传播行为判断适用范围，不以加一句提示推定所有义务完成。
- [中文 BERT 原模型卡](https://huggingface.co/hfl/chinese-roberta-wwm-ext-large)。

## 已落实与剩余动作

已保留 AGPL 与第三方许可文件，并补充中英文模型作者署名、AI 合成提示及非官方关系说明。构建收据记录权利核查状态。发布工作流创建 GitHub 草稿，实际公开由项目作者决定。

需要扩大到模型镜像、权重再分发或其他用途时，先取得并存档适用于该用途的权利依据。RIGHTS-REQUESTS.md 已准备询问信，尚未发送。作者只能许可自己拥有或被授权转授的权利；没有回复不视为同意。若无法取得许可，要公开发布就须由项目作者决定是否改用原创角色、原创图标及具有明确声音合成授权的声音，这会改变当前 BT 核心要求，未擅自实施。

核查范围：本地 0.7.1 发行包、引用来源及面向 GitHub/Codex 分发的当前设计，重点适用中国声音/个人信息规则及来源平台政策；不是全球所有法域、未来用途或未披露素材的零风险保证。

## 公开说明

This project is not endorsed by or affiliated with EA or its licensors.

This is an unofficial community project and is not endorsed by OpenAI. Speech is AI-generated, not an official game recording or an actor's endorsement.

中文语音来源：MiDd1Eye / Stardust_减 的 BT7274-Bert-VITS2，使用 Bert-VITS2 AI 生成；项目链接见上文。英文语音来源：DJMalachite/PiperVoiceModels，使用 Piper AI 合成。署名不代表已获角色、表演者或声音权利人的许可。
