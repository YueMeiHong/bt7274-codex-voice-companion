# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

"""Access control shared by the two loopback services; no cloud credentials."""
import hmac
import os
from pathlib import Path
import secrets

from fastapi.responses import JSONResponse

ROOT = Path(__file__).resolve().parents[1]


def token_path(service):
    if service not in {'companion', 'tts'}:
        raise ValueError('Unknown local service')
    override = os.getenv('BT_RUNTIME_DIR')
    return (Path(override) / service if override else ROOT / 'runtime' / service) / 'token'


def new_token(service):
    path = token_path(service)
    path.parent.mkdir(parents=True, exist_ok=True)
    value = secrets.token_urlsafe(32)
    path.write_text(value, encoding='utf8')
    return value


def tts_headers():
    return {'X-BT-Token': token_path('tts').read_text(encoding='utf8').strip()}


def secure_loopback(app, port, token, max_body=16_100_000):
    hosts = {f'127.0.0.1:{port}', f'localhost:{port}'}
    origins = {'http://' + host for host in hosts}

    @app.middleware('http')
    async def protect(request, call_next):
        if request.headers.get('host') not in hosts:
            return JSONResponse({'error': 'Local host required'}, status_code=403)
        origin = request.headers.get('origin')
        if (origin and origin not in origins) or request.headers.get('sec-fetch-site') == 'cross-site':
            return JSONResponse({'error': 'Local origin required'}, status_code=403)
        public = request.method == 'GET' and request.url.path in {'/', '/health'}
        supplied = request.headers.get('x-bt-token', '')
        if not public and not hmac.compare_digest(supplied.encode(), token.encode()):
            return JSONResponse({'error': 'BT token required'}, status_code=403)
        size = request.headers.get('content-length')
        if size is not None and (not size.isdecimal() or int(size) > max_body):
            return JSONResponse({'error': 'Request too large'}, status_code=413)
        body = bytearray()
        async for chunk in request.stream():
            if len(body) + len(chunk) > max_body:
                return JSONResponse({'error': 'Request too large'}, status_code=413)
            body.extend(chunk)
        request._body = bytes(body)
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response
