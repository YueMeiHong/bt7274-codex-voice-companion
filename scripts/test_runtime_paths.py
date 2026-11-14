# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import runtime_paths as r

class RuntimePathTests(unittest.TestCase):
    def test_relocated_install_uses_its_own_paths(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).resolve();python=root/'.venv-local/Scripts/python.exe';python.parent.mkdir(parents=True);python.touch()
            r.configure(root,python='.venv-local/Scripts/python.exe')
            result=r.mcp_config(root)['mcpServers']['bt_companion_level25']
            self.assertEqual(Path(result['command']),python)
            self.assertEqual(Path(result['args'][0]),root/'plugin/bt-companion/server.py')
            self.assertNotIn('All_Ai_Projects',json.dumps(result))

    def test_configured_models_are_used_without_copying(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).resolve();r.configure(root,tts='models/tts',asr='models/asr')
            self.assertEqual(r.tts_directory(root),root/'models/tts')
            self.assertEqual(r.asr_directory(root),root/'models/asr')
            missing=r.missing_assets(root)
            self.assertIn('BT voice weights',missing)
            self.assertIn('ASR model',missing)

    def test_missing_dependencies_produce_actionable_error(self):
        with tempfile.TemporaryDirectory() as d,patch.object(r.importlib.util,'find_spec',return_value=None):
            with self.assertRaisesRegex(r.RuntimeDependencyError,'Install-BT.ps1 -Install'):
                r.require_runtime(d)
            result=r.check(d)
            self.assertIn('mcp',result['missing_modules'])
            self.assertFalse(result['python_exists'])

    def test_full_preflight_passes_with_expected_files_and_modules(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).resolve();python=root/'.venv-local/Scripts/python.exe';python.parent.mkdir(parents=True);python.touch()
            r.configure(root,python='.venv-local/Scripts/python.exe')
            for filename in r.missing_assets(root).values():
                p=Path(filename);p.parent.mkdir(parents=True,exist_ok=True);p.touch()
            with patch.object(r.importlib.util,'find_spec',return_value=object()):
                self.assertFalse(r.require_runtime(root)['missing_modules'])

    def test_minimal_requirements_exclude_old_chat_provider_sdks(self):
        text='\n'.join(r.CORE_REQUIREMENTS+r.VOICE_REQUIREMENTS)
        for unused in ['anthropic','cartesia','elevenlabs','letta','duckduckgo']:
            self.assertNotIn(unused,text)

if __name__=='__main__':unittest.main()
