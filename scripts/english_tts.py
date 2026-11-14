# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

"""Pretrained English BT community voice, independent of Chinese synthesis."""
import asyncio
import io
from pathlib import Path
import threading
import wave
from model_integrity import verify_model

ROOT=Path(__file__).resolve().parents[1]
MODEL=ROOT/'engines/piper-bt-english/PiperVoiceModels-main/Titanfall2/BT7274/BT7274.onnx'
_lock=threading.Lock()
_voice=None

class EnglishTTSError(RuntimeError):pass

def validate_wav(data):
    try:
        with wave.open(io.BytesIO(data),'rb') as audio:
            result={'sample_rate':audio.getframerate(),'channels':audio.getnchannels(),'frames':audio.getnframes(),'sample_width':audio.getsampwidth()}
            pcm=audio.readframes(audio.getnframes())
    except (wave.Error,EOFError) as exc:raise EnglishTTSError('英文引擎未返回有效 PCM WAV') from exc
    if result['frames']<100 or not pcm or not any(pcm):raise EnglishTTSError('英文引擎返回空音频或静音')
    result['duration_seconds']=result['frames']/result['sample_rate']
    return result

def _synthesize(text):
    global _voice
    if not isinstance(text,str) or not text.strip():raise ValueError('英文文本不能为空')
    if len(text)>3000:raise ValueError('英文合成文本过长')
    if not MODEL.is_file():raise EnglishTTSError('英文 BT 社区模型未安装，请运行 Setup-English-BT.ps1')
    with _lock:
        if _voice is None:
            verify_model('english_bt', MODEL.parent)
            from piper import PiperVoice
            _voice=PiperVoice.load(MODEL,use_cuda=False)
        out=io.BytesIO()
        with wave.open(out,'wb') as audio:_voice.synthesize_wav(text,audio)
        data=out.getvalue();validate_wav(data);return data

async def synthesize(text):return await asyncio.to_thread(_synthesize,text)

if __name__=='__main__':
    import argparse,json
    parser=argparse.ArgumentParser();parser.add_argument('text');parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    raw=asyncio.run(synthesize(args.text));args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_bytes(raw);print(json.dumps(validate_wav(raw)))
