# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

"""Reuse the desktop app's shipped MCP connector, without starting an agent."""
import os
import json
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class NativeCodex:
    def __init__(self):
        self.client = None
        self.last_error = None
        self.caller = os.getenv('CODEX_THREAD_ID') or os.getenv('CODEX_SESSION_ID')

    async def connect(self, stack):
        if not self.caller or not os.getenv('CODEX_APP_TOOLS_PIPE_PATH'):
            raise RuntimeError('请在 Codex 桌面内启动 BT 插件，以连接桌面会话。')
        versions = list((Path.home()/'.codex/plugins/cache/openai-bundled/codex-app-tools').glob('*/server.mjs'))
        if not versions:
            raise RuntimeError('找不到 Codex 桌面的会话工具插件。')
        script = max(versions, key=lambda p:p.stat().st_mtime)
        params = StdioServerParameters(command='cmd.exe', args=['/d','/s','/c','call',
            str(script.parent/'scripts/launch_codex_app_tools_mcp.cmd'), str(script)],
            cwd=str(script.parent), env=dict(os.environ))
        r,w = await stack.enter_async_context(stdio_client(params))
        self.client = await stack.enter_async_context(ClientSession(r,w))
        await self.client.initialize()
        inventory=await self.client.list_tools()
        if 'list_threads' not in {tool.name for tool in inventory.tools}:
            raise RuntimeError('当前 Codex 会话工具接口不兼容；BT 配置已保留，请更新适配器。')

    async def call(self, name, args):
        if name not in {'list_threads','read_thread','send_message_to_thread'}:
            raise ValueError('Unsupported desktop operation')
        if self.client is None:
            raise RuntimeError('未连接 Codex 桌面，请从 Codex 插件启动 BT。')
        try:
            result = await self.client.call_tool(name,args,meta={'openai/threadId':self.caller})
        except Exception as exc:
            self.last_error=type(exc).__name__
            raise
        if result.is_error:
            self.last_error='Desktop request failed'
            raise RuntimeError('Codex 桌面拒绝了请求：'+str(result.content))
        self.last_error=None
        for content in result.content:
            if content.type == 'text':
                try:
                    return json.loads(content.text)
                except ValueError:
                    continue
        return {'result':'ok'}

    async def threads(self):
        data = await self.call('list_threads',{'limit':50})
        pinned=data.get('pinnedThreads',[])
        rows = pinned + data.get('threads',[])
        pinned_ids={r.get('id') for r in pinned}
        unique = {}
        for row in rows:
            if row.get('kind') == 'codex':
                if row['id'] not in unique:
                    unique[row['id']] = {k:row.get(k) for k in ['id','title','hostId']}
                    unique[row['id']]['pinned']=row['id'] in pinned_ids
        return list(unique.values())

    async def read(self, tid, host=None):
        args = {'threadId':tid,'turnLimit':2,'includeOutputs':False,'maxOutputCharsPerItem':20000}
        if host: args['hostId']=host
        return await self.call('read_thread',args)

    async def send(self, tid, text, host=None):
        args = {'threadId':tid,'prompt':text}
        if host: args['hostId']=host
        # Preserve the target's model, reasoning effort, workspace and permissions.
        return await self.call('send_message_to_thread',args)


def final_answer(data):
    for turn in data.get('turns',[]):
        if turn.get('status') in {'failed','interrupted'}:
            status=turn['status']
            return {'id':turn['id']+':'+status,'turn_id':turn['id'],
                    'text':'Codex 这次任务'+('失败' if status=='failed' else '已中断')+'。'+str(turn.get('error') or '')}
        if turn.get('status') != 'completed':
            continue
        messages = [i for i in turn.get('items',[]) if i.get('type') == 'agentMessage'
                    and i.get('phase') == 'final_answer']
        if messages:
            message = messages[-1]
            return {'id':message['id'],'text':message.get('text',''),'turn_id':turn['id']}
    return None
