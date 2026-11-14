# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

import io
import tempfile
import types
from pathlib import Path
import unittest
from unittest.mock import Mock,patch
import numpy as np
import soundfile as sf
from windows_audio import play_wav

class WindowsPlaybackTests(unittest.TestCase):
    def test_playback_without_snd_sync_and_volume_scaling(self):
        raw=io.BytesIO();sf.write(raw,np.full(100,.4),16000,format='WAV')
        win=types.SimpleNamespace(SND_FILENAME=1,SND_NODEFAULT=2,PlaySound=Mock())
        with tempfile.TemporaryDirectory() as d,patch.dict('sys.modules',{'winsound':win}):
            p=Path(d)/'test.wav';play_wav(raw.getvalue(),50,p)
            win.PlaySound.assert_called_once_with(str(p),3)
            samples,_=sf.read(p);self.assertAlmostEqual(float(samples[0]),.2,places=3)

if __name__=='__main__':unittest.main()
