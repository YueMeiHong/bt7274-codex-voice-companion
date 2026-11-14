# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

import unittest
from pathlib import Path
from speech_text import normalize_for_speech, spoken_text, segment_complete_sentences



class SpeechRegression(unittest.TestCase):
    def test_level_and_terms_do_not_become_letter_soup(self):
        self.assertEqual(spoken_text('当前是Level 1语音闲聊，TTS在本地运行。'),
                         '当前是一级语音闲聊，语音合成在本地运行。')
        self.assertEqual(spoken_text('Level一、level 2、L3'), '一级、二级、三级')

    def test_identifiers_percentages_and_negative_numbers_keep_meaning(self):
        self.assertEqual(spoken_text('BT-7274，v1.2.1，75%，-0.8。'),
                         '比提七二七四，版本一点二点一，百分之七十五，负零点八。')

    def test_dictionary_matches_whole_terms_not_substrings(self):
        _, unknown = normalize_for_speech('myAPIclient与API不同')
        self.assertIn('myAPIclient', unknown)
        self.assertNotIn('API', unknown)

    def test_normalization_is_idempotent(self):
        text = spoken_text('Level 1、TTS、BT7274，版本1.2.1。')
        self.assertEqual(spoken_text(text), text)

    def test_trailing_decimal_dot_waits_for_next_token(self):
        self.assertEqual(segment_complete_sentences('耗时0.'), ([], '耗时0.'))
        self.assertEqual(segment_complete_sentences('耗时0.8秒。下一句'), (['耗时0.8秒。'], '下一句'))

    def test_current_sentence_splitter_does_not_cut_numbers(self):
        text = '版本是1.2.1，响应时间约0.8秒，完成度是75%。铁驭，我在听。'

        # Level 2.5 directly uses our speech helper, not the historical
        # Open-LLM-VTuber streaming pipeline retained in Level 1/2.
        parts,tail=segment_complete_sentences(text)
        self.assertEqual(tail,'')
        self.assertEqual(parts, ['版本是1.2.1，响应时间约0.8秒，完成度是75%。', '铁驭，我在听。'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
