# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock,patch
import voice_state
from fastapi import HTTPException

class VoiceWorkflowTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        path=Path(__file__).with_name('companion_service.py')
        with patch.dict(os.environ,{'BT_RUNTIME_DIR':self.temp.name}):
            spec=importlib.util.spec_from_file_location('bt_voice_test',path)
            self.service=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.service)
        self.target={'id':'selected-chat','hostId':'local','enabled':True,'mode':'talk'}
        self.config={'selected':'selected-key','conversations':{'selected-key':self.target}}

    def tearDown(self):self.temp.cleanup()

    async def test_explicit_draft_send_uses_selected_original_chat(self):
        draft={'target':'selected-chat','text':'原样转写','id':'draft-1'}
        with patch.object(self.service.conversation_settings,'read',return_value=self.config),patch.object(self.service.voice_state,'read',return_value=draft),patch.object(self.service.voice_state,'write') as write,patch.object(self.service.native,'send',new_callable=AsyncMock) as send:
            result=await self.service.perform('send_draft',{})
            send.assert_awaited_once_with('selected-chat','原样转写','local')
            write.assert_called_once_with(text='',status='草稿已发送')
            self.assertIn('已发送',result['message'])

    async def test_target_change_or_reply_only_cannot_send_draft(self):
        for text_target,mode in [('old-chat','talk'),('selected-chat','reply')]:
            self.target['mode']=mode
            with patch.object(self.service.conversation_settings,'read',return_value=self.config),patch.object(self.service.voice_state,'read',return_value={'target':text_target,'text':'test','id':'1'}),patch.object(self.service.native,'send',new_callable=AsyncMock) as send:
                with self.assertRaises(HTTPException):await self.service.perform('send_draft',{})
                send.assert_not_awaited()

    def test_disabled_selection_is_not_a_microphone_target(self):
        self.target['enabled']=False
        self.assertIsNone(voice_state.target(self.config))

    async def test_summary_and_engine_follow_voice_not_japanese_settings(self):
        from types import SimpleNamespace
        for voice,source,instruction in [('英文','任务完成。','Use English.'),('中文','Task complete.','Use simplified Chinese.')]:
            prefs={'speech_voice':voice,'interface_language':'日本語','summary_length':'short','volume':100,'bt_style':True}
            response=SimpleNamespace(content=b'fake-wav',raise_for_status=lambda:None)
            client=SimpleNamespace(post=AsyncMock(return_value=response))
            with patch.object(self.service,'tts_headers',return_value={'X-BT-Token':'test-token'}),patch.object(self.service.bt_settings,'read',return_value=prefs),patch.object(self.service.provider_settings,'active',return_value={}),patch.object(self.service,'complete',new_callable=AsyncMock,return_value='spoken') as summarize,patch.object(self.service,'synthesize_english',new_callable=AsyncMock,return_value=b'fake-wav') as english,patch.object(self.service,'http',client):
                await self.service.speak('test',source,bt_style=True)
                self.assertIn(instruction,summarize.call_args.args[2][0]['content'])
                self.assertEqual(english.await_count,1 if voice=='英文' else 0)
                self.assertEqual(client.post.await_count,1 if voice=='中文' else 0)

if __name__=='__main__':unittest.main()
