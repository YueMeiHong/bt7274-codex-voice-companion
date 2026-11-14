# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SHELL=shutil.which('powershell') or shutil.which('pwsh')


@unittest.skipUnless(SHELL,'PowerShell is required')
class PersistentInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='bt install ')
        self.base=Path(self.temp.name);self.source=self.base/'source';self.source.mkdir()
        self.local=self.base/'local';self.local.mkdir()
        self.destination=self.local/'BT-7274/Level25'
        self.env=dict(os.environ,LOCALAPPDATA=str(self.local))
        shutil.copyfile(ROOT/'Install-Portable.ps1',self.source/'Install-Portable.ps1')
        for name in ['Setup-Models.ps1','Install-BT.ps1','Setup-English-BT.ps1']:
            (self.source/name).write_text('# Test-only installer stub: no downloads or external state.\n',encoding='utf8')
        (self.source/'config').mkdir();(self.source/'config/voice-profile.json').write_text('{"save_recent_segments":false}')
        (self.source/'payload.txt').write_text('new public code')
        self.inventory={'files':[{'path':p.relative_to(self.source).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in self.source.rglob('*') if p.is_file()]}
        self.save_inventory()

    def save_inventory(self):
        (self.source/'package-files.json').write_text(json.dumps(self.inventory),encoding='utf8')

    def tearDown(self):self.temp.cleanup()

    def run_install(self,*args):
        return subprocess.run([SHELL,'-NoProfile','-ExecutionPolicy','Bypass','-File',str(self.source/'Install-Portable.ps1'),*args],env=self.env,capture_output=True,text=True,encoding='utf8',errors='replace')

    def test_precheck_creates_no_persistent_files(self):
        result=self.run_install('-DryRun')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertFalse(json.loads(result.stdout)['changesFiles'])
        self.assertFalse(self.destination.exists())

    def test_install_updates_public_files_preserves_keys_and_user_voice_preference(self):
        config=self.destination/'config';config.mkdir(parents=True)
        key=config/'providers.json';key.write_text('{"private":"local-test-value"}')
        preference=config/'voice-profile.json';preference.write_text('{"save_recent_segments":true}')
        result=self.run_install('-Install')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual((self.destination/'payload.txt').read_text(),'new public code')
        self.assertEqual(key.read_text(),'{"private":"local-test-value"}')
        self.assertTrue(json.loads(preference.read_text())['save_recent_segments'])

    def test_modified_public_file_is_rejected_before_copy(self):
        (self.source/'payload.txt').write_text('tampered')
        result=self.run_install('-Install')
        self.assertNotEqual(result.returncode,0)
        self.assertFalse(self.destination.exists())

    def test_inventory_cannot_escape_installation_root(self):
        outside=self.base/'outside.txt';outside.write_text('outside')
        self.inventory['files'].insert(0,{'path':'../outside.txt','sha256':hashlib.sha256(outside.read_bytes()).hexdigest()})
        self.save_inventory();result=self.run_install('-Install')
        self.assertNotEqual(result.returncode,0)
        self.assertFalse(self.destination.exists())
