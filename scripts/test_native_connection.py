# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

import importlib.util
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import AsyncMock,patch
from native_codex import NativeCodex

class ConnectionTests(unittest.IsolatedAsyncioTestCase):
    async def test_transport_failure_and_recovery_change_health_signal(self):
        native=NativeCodex()
        native.client=types.SimpleNamespace(call_tool=AsyncMock(side_effect=OSError('closed pipe')))
        with self.assertRaises(OSError):await native.call('list_threads',{})
        self.assertEqual(native.last_error,'OSError')
        native.client.call_tool=AsyncMock(return_value=types.SimpleNamespace(is_error=False,content=[]))
        await native.call('list_threads',{})
        self.assertIsNone(native.last_error)

    def test_saved_enabled_session_restores_service_without_current_chat(self):
        path=Path(__file__).resolve().parents[1]/'plugin/bt-companion/server.py'
        spec=importlib.util.spec_from_file_location('bt_recovery_test',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as d,patch.object(module,'ROOT',Path(d)),patch.dict(os.environ,{'CODEX_APP_TOOLS_PIPE_PATH':'test'},clear=True):
            with patch.object(module.conversation_settings,'read',return_value={'conversations':{'a':{'id':'saved-id','enabled':True}}}),patch.object(module,'ensure_service') as ensure:
                module.restore_enabled_service()
                ensure.assert_called_once()
                self.assertEqual(os.environ['CODEX_THREAD_ID'],'saved-id')
            with patch.object(module.conversation_settings,'read',return_value={'conversations':{}}),patch.object(module,'ensure_service') as ensure:
                module.restore_enabled_service()
                ensure.assert_not_called()

if __name__=='__main__':unittest.main()
