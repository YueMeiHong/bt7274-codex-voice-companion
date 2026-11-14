# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

import io
import unittest
import wave
from unittest.mock import patch
import english_tts

class EnglishCommunityVoiceTests(unittest.TestCase):
    def test_missing_model_has_no_cross_language_or_system_fallback(self):
        with patch.object(english_tts,'MODEL') as model:
            model.is_file.return_value=False
            with self.assertRaises(english_tts.EnglishTTSError):english_tts._synthesize('Pilot, link established.')

    def test_original_english_text_reaches_pretrained_voice_unchanged(self):
        class Voice:
            def synthesize_wav(self,text,audio):
                self.text=text;audio.setparams((1,2,22050,0,'NONE','not compressed'));audio.writeframes(b'\x10\x00'*22050)
        voice=Voice()
        with patch.object(english_tts,'_voice',voice),patch.object(english_tts,'MODEL') as model:
            model.is_file.return_value=True
            raw=english_tts._synthesize('Pilot, link established.')
        self.assertEqual(voice.text,'Pilot, link established.')
        self.assertEqual(english_tts.validate_wav(raw)['sample_rate'],22050)

if __name__=='__main__':unittest.main()
