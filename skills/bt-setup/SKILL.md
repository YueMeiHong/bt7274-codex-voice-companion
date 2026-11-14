---
name: bt-setup
description: Install or repair BT-7274 local speech dependencies and pinned models after adding its Codex marketplace, or explain first-time BT setup. Use when BT reports first-install status or the user asks to install, configure, upgrade or repair BT.
---

# Set up BT on this computer

The plugin runs locally on Windows. Resolve the package root as two directories
above this SKILL.md. Read that root's README.md and MODEL-SETUP.md. Use the actual
absolute package path in commands; never substitute the author's development path.

1. Check Windows, Python 3.12, Git/Git LFS, and Codex desktop/CLI. Keep other plugins
   and other BT versions unchanged. Explain which prerequisite is missing and
   help install it using the user's approved method if necessary.
2. A user request to install BT authorizes the documented local dependencies and
   model downloads. Do not download anything merely because this skill is read.
   For a Git marketplace installation run `Install-Portable.ps1 -Install` from
   the actual cached package root. It validates the public file inventory and
   installs into `%LOCALAPPDATA%/BT-7274/Level25`, outside the replaceable plugin
   cache, preserving user config/models on upgrades. It installs both voices.
   For a standalone source ZIP use `Setup-Models.ps1 -Download` (or explicitly
   provided existing model paths), then `Install-BT.ps1 -Install -RequireModels`
   and `Setup-English-BT.ps1` in that source folder to register the local marketplace.
3. Keep model sources and notices;
   use pinned revisions and the integrity checks. Do not bypass a checksum failure.
   Do not import `.env`, other projects' Keys, private chats or recordings.
4. API Keys are optional for local speech. If the user wants cloud summaries,
   direct them to the native BT settings to enter their own provider information.
   Do not ask them to paste a Key into chat. Preserve local config on upgrades.
5. After dependencies are ready, reload the plugin using supported host controls
   or explain that the active session needs to reconnect. Do not force-close Codex.
   Verify tool discovery and a harmless settings/status read. Do not open the
   microphone, send chat messages, start playback or enable cloud summaries just
   to prove installation. Report the actual results and any concrete error.

Normal use: Codex → Plugins → BT-7274 → Manage. The user explicitly selects a chat
and enables BT. The plugin does not change the chat's model, permissions or folder.
