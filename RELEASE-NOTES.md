# BT-7274 Voice Companion 0.7.1 — preview

A Windows-local Codex speech companion with native settings in Chinese, English
and Japanese; local Chinese and English voices; microphone drafts and per-chat
settings; and optional user-selected provider summaries.

This release includes complete source installation, a repo marketplace, first-run
setup guidance, AGPLv3 and upstream notices, model integrity checks, loopback
authentication, private event logs and automated source/package checks.

Models and Python dependencies are downloaded separately. No model weights,
environment, API Keys, recordings, chat history or personal settings are bundled.
Japanese settings do not imply Japanese speech. Already-open settings pages are
not promised to update live. Local MCP runtime requires the Codex desktop app.

Install from the complete source package using README.md, or add the Git repository
as a marketplace and run the packaged bt-setup skill. Do not install just the nested
plugin subdirectory. See THIRD_PARTY_NOTICES.md for model/code licensing details.
