# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors
import asyncio
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from validate_publication import validate

ROOT=Path(__file__).resolve().parents[1]


class PublicationTests(unittest.TestCase):
    def test_current_manifest_catalog_runtime_and_license_agree(self):
        self.assertTrue(validate(ROOT)['passed'])

    def test_bootstrap_is_dependency_free_read_only_and_has_no_audio_tools(self):
        spec=importlib.util.spec_from_file_location('bt_bootstrap_test',ROOT/'scripts/bootstrap_mcp.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        tools=module.respond({'id':1,'method':'tools/list'})['result']['tools']
        self.assertEqual([t['name'] for t in tools],['bt_setup_status'])
        self.assertTrue(tools[0]['annotations']['readOnlyHint'])
        self.assertFalse(tools[0]['annotations']['openWorldHint'])
        self.assertEqual(module.respond({'id':2,'method':'tools/call','params':{'name':'speak'}})['error']['code'],-32602)


class BootstrapProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_mcp_handshake_before_dependency_install_in_relocated_package(self):
        with tempfile.TemporaryDirectory(prefix='bt cache ') as folder:
            root=Path(folder).resolve();(root/'scripts').mkdir()
            script=root/'scripts/bootstrap_mcp.py'
            script.write_bytes((ROOT/'scripts/bootstrap_mcp.py').read_bytes())
            async with stdio_client(StdioServerParameters(command=sys.executable,args=[str(script)],cwd=str(root))) as (reader,writer):
                async with ClientSession(reader,writer) as session:
                    await session.initialize()
                    tools=await session.list_tools()
                    self.assertEqual([t.name for t in tools.tools],['bt_setup_status'])
                    result=await session.call_tool('bt_setup_status',{})
                    self.assertFalse(result.is_error)
                    self.assertIn(str(root),result.content[0].text)
            self.assertEqual(sorted(p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()),['scripts/bootstrap_mcp.py'])
