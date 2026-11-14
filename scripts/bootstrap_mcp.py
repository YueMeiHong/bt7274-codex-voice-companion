# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors
"""Read-only MCP first-install status, using only the Python standard library."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTION = 'Explain BT first-install prerequisites and the bundled setup skill. Does not download, record audio, read chats or change configuration.'


def respond(request):
    ident = request.get('id')
    if ident is None:
        return None
    method = request.get('method')
    params = request.get('params') or {}
    result = {}
    if method == 'initialize':
        result = {'protocolVersion': params.get('protocolVersion', '2025-06-18'),
                  'capabilities': {'tools': {}}, 'serverInfo': {'name': 'bt-first-install', 'version': '0.7.1'}}
    elif method == 'tools/list':
        result = {'tools': [{'name': 'bt_setup_status', 'description': DESCRIPTION,
                            'inputSchema': {'type': 'object', 'properties': {}, 'additionalProperties': False},
                            'annotations': {'readOnlyHint': True, 'destructiveHint': False, 'openWorldHint': False}}]}
    elif method == 'tools/call':
        if params.get('name') != 'bt_setup_status':
            return {'jsonrpc': '2.0', 'id': ident, 'error': {'code': -32602, 'message': 'Unknown tool'}}
        text = ('BT first-time setup is not complete. Use the bundled bt-setup skill. '
                'Install Python dependencies and the pinned models on this computer; no cloud Key is needed for local speech. '
                'Do not claim microphone or speech readiness yet. Package root: ' + str(ROOT))
        result = {'content': [{'type': 'text', 'text': text}], 'isError': False}
    elif method == 'resources/list':
        result = {'resources': []}
    elif method == 'resources/templates/list':
        result = {'resourceTemplates': []}
    elif method == 'prompts/list':
        result = {'prompts': []}
    elif method != 'ping':
        return {'jsonrpc': '2.0', 'id': ident, 'error': {'code': -32601, 'message': 'Method not found'}}
    return {'jsonrpc': '2.0', 'id': ident, 'result': result}


def main():
    while True:
        raw = sys.stdin.buffer.readline(1_048_577)
        if not raw:
            return
        if len(raw) > 1_048_576:
            return
        try:
            request = json.loads(raw)
            if not isinstance(request, dict):
                continue
            response = respond(request)
        except (ValueError, TypeError, AttributeError):
            response = {'jsonrpc': '2.0', 'id': None, 'error': {'code': -32700, 'message': 'Invalid JSON-RPC request'}}
        if response is not None:
            sys.stdout.buffer.write((json.dumps(response, ensure_ascii=True) + '\n').encode('utf8'))
            sys.stdout.buffer.flush()


if __name__ == '__main__':
    main()
