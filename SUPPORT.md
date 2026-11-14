# Support / 使用帮助

如发现版权、署名或引用来源有误，请通过项目 Issues 告知维护者，并附上相关页面或文件位置。维护者会核实并修正。兼容性与多语言更新视维护时间而定，欢迎提交修复与翻译。

Please report copyright, credit or source attribution errors through the project's Issues page and identify the affected page or file. The maintainer will review and correct confirmed errors. Compatibility and translation updates depend on maintainer availability. Community fixes and translations are welcome.

Read README.md, MODEL-SETUP.md and the bundled bt-setup skill first. English and
Japanese setup instructions are in README.en.md and README.ja.md.

For an installation failure, provide Windows/Python/Codex versions, BT version,
the failed command and the error type. For native settings, include the affected
language and control. Before attaching screenshots/logs, remove API Keys, local
tokens, chat titles/IDs, private paths and transcript text. Never attach .env,
providers.json, conversation-settings.json, raw runtime logs or recordings.

After the repository is published, use its Issues tab for ordinary bugs and
feature requests. Security disclosures follow SECURITY.md. This community project
does not offer a response-time or service-level guarantee.

常见处理：首次安装运行 bt-setup；模型校验失败时核对固定版本，不跳过校验；修改
设置后关闭再打开原生管理页；升级代码后重新连接插件，不强制结束正在执行的 Codex
任务。其他应用或旧 BT 版本占用端口时，先确认是哪一个进程，不批量关闭 Python。
