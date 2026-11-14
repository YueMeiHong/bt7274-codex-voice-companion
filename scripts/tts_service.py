# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

"""Small local API adapter around the original MiDd1Eye BT Bert-VITS2 model.

Inference network/text pipeline are reused unchanged. No training or cloud TTS.
"""
from __future__ import annotations

import io
import json
import os
import re
import sys
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
from runtime_paths import tts_directory
from model_integrity import verify_model
from local_security import new_token, secure_loopback
SOURCE = tts_directory()
verify_model('chinese_bt', SOURCE)
os.chdir(SOURCE)
sys.path.insert(0, str(SOURCE))
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ['TRANSFORMERS_OFFLINE'] = '1'

import numpy as np
import torch
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from scipy.io import wavfile
from speech_text import normalize_for_speech, spoken_text

_engine = None
_lock = threading.Lock()
_last_metrics = {}
_record_sequence = time.time_ns() % 40


def load_profile():
    return json.loads((ROOT / 'config/voice-profile.json').read_text(encoding='utf-8'))


def record_segment(audio, original, spoken, unknown, metrics, profile):
    """Local-only rotating slots: record BT output, never microphone recordings."""
    global _record_sequence
    if not profile.get('save_recent_segments', False):
        return
    directory = ROOT / 'runtime/voice_history'
    directory.mkdir(parents=True, exist_ok=True)
    slots = max(1, min(100, int(profile.get('recent_segment_slots', 40))))
    slot = _record_sequence % slots
    _record_sequence += 1
    name = f'segment-{slot:02d}'
    (directory / f'{name}.wav').write_bytes(audio)
    item = {'time': time.strftime('%Y-%m-%d %H:%M:%S'), 'original_text': original,
            'spoken_text': spoken, 'unknown_english_words': unknown, 'metrics': metrics,
            'profile': profile, 'audio_file': f'{name}.wav'}
    (directory / f'{name}.json').write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding='utf-8')


class BTEngine:
    def __init__(self):
        import commons
        import utils
        import logging
        logging.getLogger().setLevel(logging.WARNING)
        from models import SynthesizerTrn
        from text.symbols import symbols

        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        torch.set_num_threads(4)
        self.hps = utils.get_hparams_from_file(str(SOURCE / "configs/config.json"))
        h = self.hps
        self.net = SynthesizerTrn(
            len(symbols), h.data.filter_length // 2 + 1,
            h.train.segment_size // h.data.hop_length,
            n_speakers=h.data.n_speakers, **h.model,
        ).to(self.device).eval()
        # Explicit restricted loading: never fall back to arbitrary pickle execution.
        checkpoint = torch.load(SOURCE / "logs/bt/bt.pth", map_location="cpu", weights_only=True)
        # The author's loader ignores checkpoint-only conditioning tensors.
        # Match that behavior, while requiring EVERY runtime tensor to exist.
        expected = set(self.net.state_dict())
        stored = checkpoint["model"]
        missing = expected - stored.keys()
        if missing:
            raise RuntimeError(f"BT checkpoint lacks {len(missing)} required tensors")
        self.net.load_state_dict({k: stored[k] for k in expected}, strict=True)
        del checkpoint
        self.commons = commons
        self.sr = h.data.sampling_rate

    def synthesize(self, text: str, speed: float = 1.0, profile=None, seed=None):
        from text import cleaned_text_to_sequence, get_bert
        from text.cleaner import clean_text

        profile = profile or load_profile()
        text = spoken_text(text)
        if not text or not re.search(r"[\u4e00-\u9fff0-9]", text):
            raise ValueError("没有可朗读的文字")
        norm, phones, tones, word2ph = clean_text(text, "ZH")
        phones, tones, lang = cleaned_text_to_sequence(phones, tones, "ZH")
        if self.hps.data.add_blank:
            phones = self.commons.intersperse(phones, 0)
            tones = self.commons.intersperse(tones, 0)
            lang = self.commons.intersperse(lang, 0)
            word2ph = [n * 2 for n in word2ph]
            word2ph[0] += 1
        bert = get_bert(norm, word2ph, "ZH")
        if bert.shape[-1] != len(phones):
            raise ValueError("BT音素与文本特征长度不一致")
        with torch.inference_mode():
            if seed is not None:
                torch.manual_seed(seed)
            p = torch.tensor(phones, device=self.device).long()[None]
            t = torch.tensor(tones, device=self.device).long()[None]
            l = torch.tensor(lang, device=self.device).long()[None]
            b = bert.to(self.device)[None]
            lengths = torch.tensor([len(phones)], device=self.device).long()
            speaker = torch.tensor([0], device=self.device).long()
            audio = self.net.infer(
                p, lengths, speaker, t, l, b, sdp_ratio=profile['sdp_ratio'],
                noise_scale=profile['noise_scale'], noise_scale_w=profile['noise_scale_w'],
                length_scale=profile['length_scale'] / speed,
            )[0][0, 0].float().cpu().numpy()
        if not np.isfinite(audio).all() or not len(audio):
            raise ValueError("语音模型没有生成有效音频")
        # Tiny edge ramps reduce discontinuities between separately played chunks.
        # No denoising, reverb, pitch shifting or heavy mechanical effects.
        ramp = min(round(self.sr * profile.get('edge_fade_ms', 0) / 1000), len(audio) // 2)
        if ramp > 1:
            audio[:ramp] *= np.linspace(0, 1, ramp)
            audio[-ramp:] *= np.linspace(1, 0, ramp)
        out = io.BytesIO()
        wavfile.write(out, self.sr, (np.clip(audio, -1, 1) * 32767).astype(np.int16))
        return out.getvalue(), text, len(audio) / self.sr


@asynccontextmanager
async def lifespan(app):
    global _engine
    _engine = BTEngine()
    _engine.synthesize("铁驭，语音链路已就绪。")
    yield


app = FastAPI(title="BT-7274 local voice", lifespan=lifespan)
secure_loopback(app, 12397, new_token('tts'), max_body=16_384)


class SpeechRequest(BaseModel):
    input: str = Field(min_length=1, max_length=500)
    model: str = "bt7274-zh"
    voice: str = "bt7274"
    response_format: str = "wav"
    speed: float = Field(default=1.0, ge=0.7, le=1.4)


@app.get("/health")
def health():
    return {"ready": _engine is not None, "voice": "BT7274-Bert-VITS2",
            "device": _engine.device if _engine else None,
            "sample_rate": _engine.sr if _engine else None,
            "profile": load_profile()['name'], "last": _last_metrics}


@app.post("/v1/audio/speech")
def speech(body: SpeechRequest):
    global _last_metrics
    if body.response_format != "wav":
        raise HTTPException(400, "本地BT适配器输出格式为wav")
    if body.model != "bt7274-zh" or body.voice != "bt7274":
        raise HTTPException(400, "未知BT模型或声音")
    try:
        with _lock:
            started = time.perf_counter()
            profile = load_profile()
            audio, spoken, seconds = _engine.synthesize(body.input, body.speed, profile=profile)
            _last_metrics = {"render_seconds": round(time.perf_counter() - started, 3),
                             "audio_seconds": round(seconds, 3), "characters": len(spoken)}
            try:
                _, unknown = normalize_for_speech(body.input)
                record_segment(audio, body.input, spoken, unknown, _last_metrics, profile)
            except OSError:
                import logging
                logging.warning('BT voice sample could not be saved; playback continues.')
        return Response(audio, media_type="audio/wav")
    except (ValueError, AssertionError) as e:
        raise HTTPException(422, str(e)) from None


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=12397, log_level="warning")
