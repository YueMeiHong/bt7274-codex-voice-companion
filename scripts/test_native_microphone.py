# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

import io
import threading
import unittest
import wave
import numpy as np
from native_microphone import VoiceSegmenter,NativeMicrophone,MicrophoneError


def voice(seconds):
    t=np.arange(round(seconds*16000))/16000
    return (.15*np.sin(2*np.pi*220*t)).astype('float32')

class FakeStream:
    def __init__(self,**options):self.options=options;self.started=False;self.closed=False
    def start(self):self.started=True
    def stop(self):self.started=False
    def close(self):self.closed=True
    def push(self,audio):self.options['callback'](audio.reshape(-1,1),len(audio),None,None)

class SegmenterTests(unittest.TestCase):
    def test_silence_only_and_short_click_are_not_utterances(self):
        vad=VoiceSegmenter()
        self.assertEqual(vad.feed(np.zeros(32000)),[])
        self.assertEqual(vad.feed(np.r_[voice(.02),np.zeros(16000)]),[])

    def test_silence_termination_and_wav_format(self):
        vad=VoiceSegmenter();self.assertEqual(vad.feed(voice(.4)),[])
        clips=vad.feed(np.zeros(16000));self.assertEqual(len(clips),1)
        self.assertAlmostEqual(len(clips[0])/16000,1.3,places=2)

    def test_maximum_bounds_continuous_speech(self):
        vad=VoiceSegmenter(max_seconds=1)
        clips=vad.feed(voice(2.5))
        self.assertEqual(len(clips),2)
        self.assertTrue(all(len(c)==16000 for c in clips))

class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.created=[]
        def factory(**kwargs):
            stream=FakeStream(**kwargs);self.created.append(stream);return stream
        self.mic=NativeMicrophone(queue_size=1,stream_factory=factory)

    def utterance(self):self.created[-1].push(np.r_[voice(.3),np.zeros(16000)].astype('float32'))

    def test_default_off_idempotent_start_and_pcm16_clip(self):
        self.assertFalse(self.mic.status['running']);self.assertEqual(self.created,[])
        self.mic.start();self.mic.start();self.assertEqual(len(self.created),1)
        self.utterance();clip=self.mic.pop_clip()
        with wave.open(io.BytesIO(clip),'rb') as w:
            self.assertEqual((w.getframerate(),w.getnchannels(),w.getsampwidth()),(16000,1,2))
        self.assertIsNone(self.mic.pop_clip());self.mic.stop()

    def test_queue_is_bounded_and_stop_clears_old_target_audio(self):
        self.mic.start();self.utterance();self.utterance()
        self.assertEqual(self.mic.status['queued'],1);self.assertEqual(self.mic.status['dropped'],1)
        old=self.created[-1];self.mic.stop();old.push(voice(1))
        self.assertIsNone(self.mic.pop_clip());self.mic.start()
        self.assertIsNone(self.mic.pop_clip());self.mic.stop()

    def test_speaking_suppression_discards_echo(self):
        self.mic.start();self.utterance();self.mic.suppress(True);self.utterance()
        self.assertIsNone(self.mic.pop_clip());self.mic.suppress(False);self.utterance()
        self.assertIsNotNone(self.mic.pop_clip());self.mic.stop()

    def test_device_failure_is_clear_and_capture_stays_off(self):
        def fail(**kwargs):raise OSError('fake unavailable device')
        mic=NativeMicrophone(stream_factory=fail)
        with self.assertRaisesRegex(MicrophoneError,'无法打开麦克风'):mic.start()
        self.assertFalse(mic.status['running']);self.assertIn('OSError',mic.status['error'])

    def test_device_can_deliver_audio_during_start_without_locking_up(self):
        class ImmediateStream(FakeStream):
            def start(stream):
                worker=threading.Thread(target=lambda:stream.push(np.r_[voice(.3),np.zeros(16000)].astype('float32')))
                worker.start();worker.join(1)
                if worker.is_alive():raise RuntimeError('callback blocked by startup lock')
        mic=NativeMicrophone(stream_factory=ImmediateStream)
        mic.start();self.assertIsNotNone(mic.pop_clip());mic.stop()

if __name__=='__main__':unittest.main()
