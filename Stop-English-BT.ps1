# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

$ErrorActionPreference='Stop'
& (Join-Path $PSScriptRoot 'Stop-BT.ps1') -Services bt-english
