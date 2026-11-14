# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

import unittest
from voice_routing import speech_language,summary_instruction

class VoiceRoutingTests(unittest.TestCase):
    def test_explicit_voice_controls_summary_even_for_foreign_source(self):
        self.assertEqual(speech_language('中文','Task complete.'),'zh')
        self.assertEqual(speech_language('英文','任务已完成。'),'en')
        self.assertEqual(summary_instruction('zh'),'Use simplified Chinese.')
        self.assertEqual(summary_instruction('en'),'Use English.')

    def test_auto_and_legacy_names(self):
        self.assertEqual(speech_language('自动（中英）','Task complete.'),'en')
        self.assertEqual(speech_language('自动（中英）','任务已完成。'),'zh')
        self.assertEqual(speech_language('英文 BT（实验）','任务完成'),'en')
