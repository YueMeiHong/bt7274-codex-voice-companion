# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

import importlib.util
from pathlib import Path
import tempfile
from datetime import datetime
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
                self.assertNotEqual(feedback.display_result(self.profile,language,self.path),feedback.message('idle',language))
            self.assertNotIn('test-secret',self.path.read_text())

    async def test_native_settings_action_refreshes_success_and_failure(self):
        source=Path(__file__).parents[1]/'plugin/bt-companion/server.py'
        spec=importlib.util.spec_from_file_location('bt_feedback_test_server',source)
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with patch.object(feedback,'PATH',self.path), patch.object(module.provider_settings,'active',return_value=self.profile), patch.object(module,'settings_rows',new_callable=AsyncMock,return_value=[]):
            for language in ['简体中文','English','日本語']:
                preferences={**module.bt_settings.DEFAULTS,'interface_language':language}
                with patch.object(module.bt_settings,'read',return_value=preferences):
                    before=await module.bt_settings_read(None)
                    action=before['schema']['properties']['connection_test_action']
                    for error in (None,ProviderError('请先填写模型名称')):
                        with patch.object(feedback,'test_connection',new_callable=AsyncMock,side_effect=error) as test:
                            update=await module.bt_settings_update({'connection_test_action':action['enum'][1]},None)
                            test.assert_awaited_once_with(self.profile)
                        after=await module.bt_settings_read(None)
                        self.assertEqual(update['values']['connection_test_status'],after['values']['connection_test_status'])
                        self.assertEqual(after['values']['connection_test_action'],action['enum'][0])
                        code='success' if error is None else str(error)
                        self.assertIn(feedback.message(code,language),after['values']['connection_test_status'])
                        datetime.strptime(after['values']['connection_test_status'].split(' · ')[0],'%Y-%m-%d %H:%M:%S')
