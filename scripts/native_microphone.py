# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

"""Explicitly started local capture. No network, transcription, or chat access."""
from collections import deque
import asyncio
import io
import math
import queue
import threading
import wave

import numpy as np


class MicrophoneError(RuntimeError):
    pass


def wav_bytes(samples, sample_rate=16000):
    """Encode mono float audio as portable PCM16 WAV bytes."""
    pcm=np.rint(np.clip(samples,-1,1)*32767).astype('<i2').tobytes()
    result=io.BytesIO()
    with wave.open(result,'wb') as output:
        output.setnchannels(1);output.setsampwidth(2)
        output.setframerate(sample_rate);output.writeframes(pcm)
    return result.getvalue()


class VoiceSegmenter:
    """Small energy VAD with pre-roll, silence termination, and bounded clips."""
    def __init__(self,sample_rate=16000,threshold=.012,silence_seconds=.9,
                 max_seconds=45,min_voiced_seconds=.12,preroll_seconds=.16):
        if sample_rate<=0 or threshold<=0 or silence_seconds<=0 or max_seconds<=0:
            raise ValueError('音频分段参数必须为正数')
        self.sample_rate=sample_rate
        self.threshold=threshold
        self.silence_limit=round(silence_seconds*sample_rate)
        self.maximum=round(max_seconds*sample_rate)
        self.minimum_voiced=round(min_voiced_seconds*sample_rate)
        self.frame_size=max(1,round(.02*sample_rate))
        self.pre_count=max(1,math.ceil(preroll_seconds*sample_rate/self.frame_size))
        self.reset()

    def reset(self):
        self.pre=deque(maxlen=self.pre_count)
        self.frames=[];self.total=0;self.silent=0;self.voiced=0

    def feed(self,samples):
        samples=np.asarray(samples,dtype=np.float32).reshape(-1)
        completed=[]
        for offset in range(0,len(samples),self.frame_size):
            frame=samples[offset:offset+self.frame_size].copy()
            active=bool(np.sqrt(np.mean(frame*frame))>=self.threshold)
            if not self.frames:
                if not active:
                    self.pre.append(frame);continue
                self.frames=list(self.pre);self.pre.clear()
                self.total=sum(len(f) for f in self.frames)
            self.frames.append(frame);self.total+=len(frame)
            if active:self.voiced+=len(frame);self.silent=0
            else:self.silent+=len(frame)
            if self.silent>=self.silence_limit or self.total>=self.maximum:
                if self.voiced>=self.minimum_voiced:
                    completed.append(np.concatenate(self.frames)[:self.maximum])
                self.reset()
        return completed


class NativeMicrophone:
    """Thread-safe capture service; constructing this object never opens a mic.

    start()/stop() are synchronous. pop_clip() returns WAV bytes or None.
    get_clip(timeout=...) is an optional async wrapper. Queue size is bounded;
    when full, the newest complete utterance is dropped rather than blocking
    PortAudio. stop() discards captured/pending utterances for safe retargeting.
    """
    def __init__(self,device=None,*,sample_rate=16000,queue_size=3,
                 stream_factory=None,**vad_options):
        if queue_size<1:raise ValueError('语音队列大小至少为1')
        self.device=device;self.sample_rate=sample_rate
        self._factory=stream_factory
        self._clips=queue.Queue(maxsize=queue_size)
        self._lock=threading.RLock()
        self._lifecycle_lock=threading.Lock()
        self._segmenter=VoiceSegmenter(sample_rate=sample_rate,**vad_options)
        self._stream=None;self._running=False;self._generation=0
        self._error=None;self._warning=None;self._dropped=0
        self._suppressed=False

    @property
    def status(self):
        with self._lock:
            return {'running':self._running,'error':self._error,
                    'warning':self._warning,'queued':self._clips.qsize(),
                    'dropped':self._dropped,'sample_rate':self.sample_rate,
                    'suppressed':self._suppressed}

    def start(self):
        with self._lifecycle_lock:
            return self._start()

    def _start(self):
        with self._lock:
            if self._running:return self.status
            self._generation+=1;generation=self._generation
            self._clear();self._segmenter.reset()
            self._error=None;self._warning=None;self._suppressed=False
            def callback(indata,frames,time_info,status):
                with self._lock:
                    if generation!=self._generation or not self._running:return
                    if status:self._warning='麦克风输入有丢帧或设备警告'
                    if self._suppressed:return
                    try:
                        audio=np.asarray(indata,dtype=np.float32)
                        mono=audio[:,0] if audio.ndim==2 else audio
                        for clip in self._segmenter.feed(mono):
                            try:self._clips.put_nowait(wav_bytes(clip,self.sample_rate))
                            except queue.Full:self._dropped+=1
                    except Exception as exc:
                        self._error='麦克风音频处理失败：'+type(exc).__name__
        # PortAudio may invoke the callback before start() returns; never hold
        # the callback lock across device startup or shutdown.
        try:
            if self._factory is None:
                import sounddevice
                factory=sounddevice.InputStream
            else:factory=self._factory
            stream=factory(samplerate=self.sample_rate,channels=1,
                dtype='float32',blocksize=round(self.sample_rate*.02),
                device=self.device,callback=callback)
            with self._lock:self._stream=stream;self._running=True
            stream.start()
        except Exception as exc:
            with self._lock:
                self._running=False;self._generation+=1
                stream=self._stream;self._stream=None
                self._error='无法打开麦克风：请检查设备、系统权限及16kHz单声道支持（'+type(exc).__name__+'）'
            if stream is not None:
                try:stream.close()
                except Exception:pass
            raise MicrophoneError(self._error) from exc
        return self.status

    def _clear(self):
        while True:
            try:self._clips.get_nowait()
            except queue.Empty:break

    def stop(self):
        with self._lifecycle_lock:
            return self._stop()

    def _stop(self):
        # Do not hold the callback lock while waiting for PortAudio to stop.
        with self._lock:
            self._running=False;self._generation+=1
            stream=self._stream;self._stream=None
            self._clear();self._segmenter.reset();self._suppressed=False
        if stream is not None:
            try:stream.stop()
            finally:stream.close()
        return self.status

    def suppress(self,enabled=True):
        """Pause capture while speaking, clearing partial audio to avoid echo."""
        with self._lock:
            self._suppressed=bool(enabled)
            self._segmenter.reset();self._clear()

    def pop_clip(self):
        with self._lock:
            if not self._running:return None
            try:return self._clips.get_nowait()
            except queue.Empty:return None

    async def get_clip(self,timeout=None):
        loop=asyncio.get_running_loop();deadline=None if timeout is None else loop.time()+timeout
        while True:
            clip=self.pop_clip()
            if clip is not None:return clip
            if not self.status['running']:raise MicrophoneError('麦克风未开启或已停止')
            if deadline is not None and loop.time()>=deadline:raise TimeoutError('尚未取得完整语音片段')
            await asyncio.sleep(.02)
