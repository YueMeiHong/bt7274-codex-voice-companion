# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

"""Speech language is independent of the settings UI and provider profile."""
import re

def speech_language(voice,text):
    if voice in {'英文','英文 BT','英文 BT（实验）'}:return 'en'
    if voice in {'中文','中文 BT'}:return 'zh'
    return 'en' if re.search(r'[A-Za-z]',text) and not re.search(r'[\u3040-\u30ff\u4e00-\u9fff]',text) else 'zh'

def summary_instruction(language):
    return 'Use English.' if language=='en' else 'Use simplified Chinese.'
