# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import provider_settings as p


class ProviderSettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/'providers.json'

    def tearDown(self):
        self.temp.cleanup()

    def test_read_defaults_has_no_environment_or_file_side_effect(self):
        with patch.dict(os.environ,{'DEEPSEEK_API_KEY':'test-do-not-import'}):
            data=p.read(self.path)
        self.assertTrue(all(profile['api_key']=='' for profile in data['providers'].values()))
        self.assertFalse(self.path.exists())

    def test_switch_retains_separate_profiles_and_custom_values(self):
        p.update({'base_url':'https://example.test/v1/'},self.path)
        p.update({'api_key':'test-deepseek-key'},self.path)
        p.update({'model':'model-a'},self.path)
        p.update({'provider':'Ollama（本机）'},self.path)
        self.assertEqual(p.active(self.path)['api_key'],'')
        p.update({'model':'local-model:latest'},self.path)
        p.update({'provider':'deepseek'},self.path)
        active=p.active(self.path)
        self.assertEqual(active['api_key'],'test-deepseek-key')
        self.assertEqual(active['base_url'],'https://example.test/v1')
        self.assertEqual(active['model'],'model-a')
        self.assertEqual(p.read(self.path)['providers']['ollama']['model'],'local-model:latest')

    def test_empty_model_and_key_are_valid_during_setup(self):
        p.update({'model':'','api_key':''},self.path)
        self.assertEqual(p.active(self.path)['model'],'')
        self.assertEqual(p.active(self.path)['api_key'],'')

    def test_invalid_urls_and_mixed_provider_writes_are_atomic(self):
        for changes in [{'base_url':'https://user:pass@example.test/v1'},
                        {'base_url':'file:///tmp/key'}, {'base_url':'https://example.test/?key=secret'},
                        {'base_url':'http://example.test:999999'}, {'base_url':'example.test/v1'},
                        {'provider':'openai','api_key':'test-key'}, {'unknown':True}]:
            with self.assertRaises(ValueError):p.update(changes,self.path)
            self.assertFalse(self.path.exists())

    def test_native_fields_show_only_active_profile_and_runtime_standard_ids(self):
        p.update({'provider':'自定义 OpenAI 兼容','speech_language':'English'},self.path)
        p.update({'api_key':'test-local-key'},self.path)
        result=p.describe(self.path)
        self.assertEqual(set(result['values']),p.FIELDS-{'speech_language'})
        self.assertEqual(result['values']['provider'],'自定义 OpenAI 兼容')
        self.assertEqual(result['values']['api_key'],'test-local-key')
        self.assertEqual(p.active(self.path)['provider'],'custom')
        self.assertEqual(p.active(self.path)['speech_language'],'en')
        self.assertNotIn('providers',result['values'])


if __name__=='__main__':unittest.main()
