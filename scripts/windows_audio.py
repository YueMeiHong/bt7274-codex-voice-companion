# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

"""Synchronous Windows playback, with software volume and no fallback beep."""
import io
import soundfile as sf

def play_wav(raw,volume,path):
    import winsound
    samples,rate=sf.read(io.BytesIO(raw),dtype='float32')
    sf.write(path,samples*(max(0,min(100,volume))/100),rate,subtype='PCM_16')
    # Python winsound uses synchronous playback by default; SND_SYNC is not
    # exposed on all Python builds. Do not use a nonexistent constant.
    winsound.PlaySound(str(path),winsound.SND_FILENAME|winsound.SND_NODEFAULT)
