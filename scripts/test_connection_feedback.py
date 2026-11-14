# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

import importlib.util
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock,patch
import connection_feedback as feedback
from provider_client import ProviderError

class ConnectionFeedbackTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'test.json'
        self.profile={'provider':'custom','base_url':'http://localhost:1234/v1','model':'test','api_key':'test-secret'}
    def tearDown(self):self.temp.cleanup()

    async def test_success_and_changed_profile_invalidates_result(self):
        with patch.object(feedback,'test_connection',new_callable=AsyncMock):
            self.assertEqual(await feedback.run(self.profile,self.path),'success')
        self.assertEqual(feedback.read(self.profile,self.path),'success')
        self.assertEqual(feedback.read({**self.profile,'model':'another'},self.path),'idle')
        self.assertNotIn('test-secret',self.path.read_text())

    async def test_failure_is_visible_localized_and_unexpected_details_are_not_saved(self):
        for error in [ProviderError('认证失败：请检查当前服务商的 API Key 或权限'),RuntimeError('test-secret')]:
            with patch.object(feedback,'test_connection',new_callable=AsyncMock,side_effect=error):
                code=await feedback.run(self.profile,self.path)
            self.assertNotEqual(code,'success')
            for language in ['简体中文','English','日本語']:
                self.assertNotEqual(feedback.button_title(code,language),feedback.button_title('idle',language))
            self.assertNotIn('test-secret',self.path.read_text())

    async def test_native_tool_metadata_matches_language_and_publishes_result(self):
        source=Path(__file__).parents[1]/'plugin/bt-companion/server.py'
        spec=importlib.util.spec_from_file_location('bt_feedback_test_server',source)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with patch.object(feedback,'PATH',self.path),patch.object(module.provider_settings,'active',return_value=self.profile):
            for language in ['简体中文','English','日本語']:
                with patch.object(module.bt_settings,'read',return_value={'interface_language':language}):
                    feedback.write(self.profile,'idle')
                    before={t.name:t for t in await module.server.list_tools()}
                    self.assertEqual(before['bt_test_connection'].title,feedback.button_title('idle',language))
                    published=[]
                    async def notify():
                        tools={t.name:t for t in await module.server.list_tools()}
                        published.append(tools['bt_test_connection'].title)
                    ctx=SimpleNamespace(session=SimpleNamespace(send_tool_list_changed=notify))
                    with patch.object(feedback,'test_connection',new_callable=AsyncMock):
                        result=await module.bt_test_connection(ctx)
                    self.assertEqual(published,[feedback.button_title('running',language),feedback.button_title('success',language)])
                    self.assertEqual(result,feedback.message('success',language))
