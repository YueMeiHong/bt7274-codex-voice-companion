# 0.7.1 分发路线

## GitHub 仓库型 Codex marketplace

这是当前可直接准备的分发路线。完整源码根目录包含 `.agents/plugins/marketplace.json`。发布后，使用者先克隆/解压完整源码，运行模型准备与安装器；安装器登记本机 Python 和绝对路径，再把本机 marketplace 加入 Codex。本次发布改为整个源码根目录都是插件（marketplace 的 source.path 为 ./），同时保留内部适配器。Codex 从 Git 缓存安装时也会取得完整脚本和安装器。首次只暴露安装状态工具，使用内置 bt-setup 后连接本机正式服务。单独复制内部 plugin/ 子目录不属于支持的发布方式。

Codex 也支持 `codex plugin marketplace add owner/repo`，从 GitHub 仓库添加目录。不需要 OpenAI 本机 MCP 提交白名单。仓库 URL 必须等真实仓库确定后填写，不能编造。

## OpenAI Community Plugins

`openai/community-plugins` 接受外部 fork + PR，维护者审阅、CLA 和测试是独立流程。它是由 OpenAI 团队维护的 Git-backed Codex marketplace，不等于统一公共 Plugins Directory。外部贡献说明没有要求提交方先具备本机 MCP 组织白名单。BT 的依赖安装方案需要按该仓库自包含插件与主测试入口规范另做接入；本次不创建 PR、不签署 CLA。

## OpenAI 统一公共 Plugins Directory

这是第三条路线。官方 `Submit desktop-only plugins` 当前明确要求本机 stdio MCP 提交方先由 OpenAI 联系人确认资格并把组织加入 allowlist。该限制不能推广到上面两条 GitHub marketplace 路线。是否具备公共目录资格，需要账号侧事实，不能仅凭源码判断。

来源（核查 2026-11-08）：

- https://developers.openai.com/plugins/build/plugins
- https://learn.chatgpt.com/docs/developer-commands
- https://github.com/openai/community-plugins/blob/main/CONTRIBUTING.md
- https://github.com/openai/community-plugins/blob/main/README.md
- https://developers.openai.com/plugins/deploy/desktop-only

Git marketplace 用户的持久运行目录为 `%LOCALAPPDATA%/BT-7274/Level25`。Install-Portable.ps1 验证公开文件清单后更新代码，不复制或覆盖用户 providers/conversation 配置；模型和环境留在同一持久目录。插件版本变化时重新运行 bt-setup。
