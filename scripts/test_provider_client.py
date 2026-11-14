# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

import unittest
import httpx
from provider_client import complete,ProviderError

class ProviderClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_local_ollama_uses_selected_address_without_key(self):
        def handle(req):
            self.assertEqual(str(req.url),'http://localhost:11434/v1/chat/completions')
            self.assertNotIn('authorization',req.headers)
            return httpx.Response(200,json={'choices':[{'message':{'content':'OK'}}]})
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
            self.assertEqual(await complete(client,{'base_url':'http://localhost:11434/v1','api_key':'','model':'local'},[]),'OK')

    async def test_auth_error_does_not_echo_provider_response_or_key(self):
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda req:httpx.Response(401,text='private response'))) as client:
            with self.assertRaises(ProviderError) as caught:
                await complete(client,{'base_url':'https://example.test/v1','api_key':'test-only-secret','model':'test'},[])
            self.assertNotIn('test-only-secret',str(caught.exception))
            self.assertNotIn('private response',str(caught.exception))

if __name__=='__main__':unittest.main()
