# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

import httpx
from fastapi import FastAPI, Request, HTTPException
from local_security import secure_loopback
from model_integrity import verify_model


class LoopbackSecurityTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.app = FastAPI()
        secure_loopback(self.app, 12397, 'test-local-token', max_body=64)

        @self.app.get('/health')
        def health(): return {'ready': True}

        @self.app.post('/v1/audio/speech')
        async def speech(request: Request): return await request.json()

        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url='http://127.0.0.1:12397')

    async def asyncTearDown(self): await self.client.aclose()

    async def test_foreign_hosts_origins_and_cross_site_requests_fail(self):
        for headers in [{'host':'attacker.test:12397'}, {'origin':'https://attacker.test'}, {'sec-fetch-site':'cross-site'}]:
            response = await self.client.get('/health', headers=headers)
            self.assertEqual(response.status_code, 403)

    async def test_missing_wrong_token_cannot_reach_synthesis(self):
        for headers in [{}, {'X-BT-Token':'wrong'}, {'X-BT-Token':'非ASCII'}]:
            if headers.get('X-BT-Token') == '非ASCII':
                headers = {b'X-BT-Token':'非ASCII'.encode('utf8')}
            response = await self.client.post('/v1/audio/speech', headers=headers, json={'input':'test'})
            self.assertEqual(response.status_code, 403)

    async def test_authenticated_json_survives_body_limit_and_has_no_store(self):
        response = await self.client.post('/v1/audio/speech', headers={'X-BT-Token':'test-local-token'}, json={'input':'test'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'input':'test'})
        self.assertEqual(response.headers['cache-control'], 'no-store')

    async def test_declared_and_chunked_oversized_bodies_fail(self):
        headers = {'X-BT-Token':'test-local-token'}
        self.assertEqual((await self.client.post('/v1/audio/speech', headers=headers, content=b'x'*65)).status_code, 413)
        async def chunks():
            yield b'x'*40
            yield b'x'*40
        self.assertEqual((await self.client.post('/v1/audio/speech', headers=headers, content=chunks())).status_code, 413)

    async def test_docs_require_token_but_health_probe_does_not(self):
        self.assertEqual((await self.client.get('/openapi.json')).status_code, 403)
        self.assertEqual((await self.client.get('/health')).status_code, 200)


class ModelIntegrityTests(unittest.TestCase):
    def test_modified_missing_and_unlisted_model_files_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            model = root/'model';model.mkdir()
            (model/'model.py').write_bytes(b'# trusted code')
            manifest = root/'manifest.json'
            manifest.write_text(json.dumps({'chinese_bt':{'model.py':hashlib.sha256(b'# trusted code').hexdigest()}}))
            self.assertTrue(verify_model('chinese_bt',model,manifest))
            (model/'extra.py').write_text('# injected')
            with self.assertRaisesRegex(RuntimeError,'Unlisted'):verify_model('chinese_bt',model,manifest)
            (model/'extra.py').unlink()
            (model/'model.py').write_text('# tampered')
            with self.assertRaisesRegex(RuntimeError,'integrity'):verify_model('chinese_bt',model,manifest)
            (model/'model.py').unlink()
            with self.assertRaisesRegex(RuntimeError,'missing'):verify_model('chinese_bt',model,manifest)

    def test_manifest_cannot_escape_model_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);model=root/'model';model.mkdir()
            (root/'outside.py').write_bytes(b'outside')
            manifest=root/'manifest.json'
            manifest.write_text(json.dumps({'chinese_bt':{'../outside.py':hashlib.sha256(b'outside').hexdigest()}}))
            with self.assertRaisesRegex(RuntimeError,'outside'):verify_model('chinese_bt',model,manifest)


class CompanionBoundaryTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp=tempfile.TemporaryDirectory()
        with patch.dict(os.environ,{'BT_RUNTIME_DIR':self.temp.name}):
            spec=importlib.util.spec_from_file_location('bt_security_test',Path(__file__).with_name('companion_service.py'))
            self.service=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.service)

    async def asyncTearDown(self): self.temp.cleanup()

    async def test_disk_events_never_contain_transcripts_answers_or_delivery(self):
        self.service.emit('speech',original='private answer',speech='private summary',text='private transcript',result={'secret':'delivery'})
        logged=(Path(self.temp.name)/'events.jsonl').read_text(encoding='utf8')
        for secret in ['private answer','private summary','private transcript','delivery']:
            self.assertNotIn(secret,logged)

    async def test_oversized_and_invalid_action_cannot_send(self):
        with patch.object(self.service.native,'send',new_callable=AsyncMock) as send:
            for action,args in [('send',{}),('send',{'threadId':'chat','text':'x'*12001}),('speak_text',{'text':123})]:
                with self.assertRaises(HTTPException):await self.service.perform(action,args)
            send.assert_not_awaited()

    async def test_manual_speech_does_not_override_disabled_cloud_summary(self):
        prefs={'speech_voice':'英文','summary_length':'short','volume':100,'bt_style':False}
        with patch.object(self.service.bt_settings,'read',return_value=prefs),patch.object(self.service,'complete',new_callable=AsyncMock) as cloud,patch.object(self.service,'synthesize_english',new_callable=AsyncMock,return_value=b'wav') as synth:
            await self.service.speak('manual','Private answer',bt_style=True)
            cloud.assert_not_awaited()
            synth.assert_awaited_once_with('Private answer')

    async def test_target_change_while_waiting_for_send_lock_cannot_send(self):
        first={'selected':'a','conversations':{'a':{'id':'first-chat','enabled':True,'mode':'talk','hostId':'local'}}}
        changed={'selected':'b','conversations':{'b':{'id':'second-chat','enabled':True,'mode':'talk','hostId':'local'}}}
        draft={'id':'draft-1','target':'first-chat','text':'private draft'}
        with patch.object(self.service.conversation_settings,'read',side_effect=[first,changed]),patch.object(self.service.voice_state,'read',return_value=draft),patch.object(self.service.native,'send',new_callable=AsyncMock) as send:
            with self.assertRaisesRegex(HTTPException,'改变'):
                await self.service.perform('send_draft',{})
            send.assert_not_awaited()
