# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
SHELL=shutil.which('powershell') or shutil.which('pwsh')

@unittest.skipUnless(SHELL,'PowerShell is required for release builder tests')
class ReleasePackageTests(unittest.TestCase):
    def test_source_archive_contains_runtime_without_user_state(self):
        with tempfile.TemporaryDirectory() as d:
            result=subprocess.run([SHELL,'-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'Build-Release.ps1'),'-OutputDirectory',d],capture_output=True,text=True,encoding='utf8',errors='replace')
            self.assertEqual(result.returncode,0,result.stderr)
            report=json.loads(result.stdout)
            self.assertTrue(report['passed'])
            with zipfile.ZipFile(report['archive']) as archive:
                names=set(archive.namelist())
                self.assertIn('scripts/native_microphone.py',names)
                self.assertIn('Install-BT.ps1',names)
                self.assertIn('LICENSE',names)
                self.assertIn('THIRD_PARTY_NOTICES.md',names)
                self.assertIn('config/model-integrity.json',names)
                self.assertIn('scripts/local_security.py',names)
                self.assertFalse(json.loads(archive.read('config/voice-profile.json'))['save_recent_segments'])
                self.assertNotIn('scripts/english_crosslingual.py',names)
                self.assertNotIn('scripts/english_engine_assets.py',names)
                self.assertNotIn('config/providers.json',names)
                self.assertNotIn('config/conversation-settings.json',names)
                self.assertFalse(any(n.startswith(('vendor/','engines/','runtime/','.venv')) for n in names))
                config=json.loads(archive.read('plugin/bt-companion/.mcp.json'))
                server=next(iter(config['mcpServers'].values()))
                self.assertEqual(server['command'],'python')
                self.assertEqual(server['args'],['${PLUGIN_ROOT}/server.py'])

    def test_rebuilding_release_does_not_modify_local_recording_preference(self):
        before=(ROOT/'config/voice-profile.json').read_bytes()
        with tempfile.TemporaryDirectory() as d:
            result=subprocess.run([SHELL,'-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'Build-Release.ps1'),'-OutputDirectory',d],capture_output=True,text=True,encoding='utf8',errors='replace')
            self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual((ROOT/'config/voice-profile.json').read_bytes(),before)

    def test_verifier_rejects_credentials_and_user_state(self):
        with tempfile.TemporaryDirectory() as d:
            for name,content in [('config/providers.json','{}'),('scripts/bad.py','key="sk-"+""')]:
                # First case checks forbidden paths; second uses a synthetic key.
                if name.endswith('bad.py'):content='key="sk-'+('Z'*24)+'"'
                p=Path(d)/'bad.zip'
                with zipfile.ZipFile(p,'w') as archive:archive.writestr(name,content)
                result=subprocess.run([SHELL,'-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'Build-Release.ps1'),'-VerifyOnly','-ArchivePath',str(p)],capture_output=True,text=True,encoding='utf8',errors='replace')
                self.assertNotEqual(result.returncode,0)

if __name__=='__main__':unittest.main()
