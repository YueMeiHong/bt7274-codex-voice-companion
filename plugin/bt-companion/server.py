# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

"""Local desktop plugin: UI + explicit BT controls, no agent/model execution."""
import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import time
import asyncio
import httpx
from mcp.server.mcpserver import MCPServer, Context
from mcp.types import ToolAnnotations
from typing_extensions import TypedDict

PLUGIN=Path(__file__).resolve().parent
ROOT=PLUGIN.parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import bt_settings
import conversation_settings
import provider_settings
import voice_state
from localization import localize,normalize_changes,TOOLS,JP
import connection_feedback
from provider_client import test_connection,ProviderError
from native_codex import NativeCodex
from contextlib import AsyncExitStack
from filelock import FileLock
class NativeSettingsServer(MCPServer):
    async def list_tools(self):
        tools=await super().list_tools()
        language=bt_settings.read()['interface_language']
        for tool in tools:
            if tool.name=='bt_test_connection':
                tool.title=connection_feedback.button_title(connection_feedback.read(provider_settings.active()),language)
            elif language in {'English','日本語'} and tool.name in TOOLS:
                title=TOOLS[tool.name];tool.title=JP.get(title,title) if language=='日本語' else title
        return tools

READ_HINTS=ToolAnnotations(read_only_hint=True,destructive_hint=False,open_world_hint=False)
LOCAL_HINTS=ToolAnnotations(read_only_hint=False,destructive_hint=False,open_world_hint=False)
NETWORK_HINTS=ToolAnnotations(read_only_hint=False,destructive_hint=False,open_world_hint=True)

server=NativeSettingsServer('BT-7274 语音伙伴')
server._lowlevel_server.extensions['openai/settings']={'readTool':'bt_settings_read','updateTool':'bt_settings_update'}


class SettingsReadResult(TypedDict):
    schema:dict
    values:dict
    layout:list[dict]


class SettingsUpdateResult(TypedDict):
    values:dict


async def settings_rows(ctx):
    caller_context(ctx)
    async with AsyncExitStack() as stack:
        native=NativeCodex()
        await native.connect(stack)
        return await native.threads()


async def settings_description(ctx):
    result=bt_settings.describe()
    connections=provider_settings.describe()
    result['schema']['properties']={**connections['schema']['properties'],**result['schema']['properties']}
    result['values'].update(connections['values'])
    feedback=connection_feedback.message(connection_feedback.read(provider_settings.active()),bt_settings.read()['interface_language'])
    result['schema']['properties']['connection_test_status']={'type':'string','title':'连接测试结果','enum':[feedback],
        'description':'最近一次测试结果；更改连接配置后需要重新测试。按钮也会显示成功或失败；悬停查看完整结果。'}
    result['values']['connection_test_status']=feedback
    connections['layout'][0]['items'].append({'kind':'property','property':'connection_test_status'})
    connections['layout'][0]['items'].append({'kind':'tool','tool':'bt_test_connection','title':'测试当前连接','description':'由本机向所选服务发送一条简短测试请求。'})
    result['layout']=connections['layout']+result['layout']
    result['layout'].append({'kind':'group','title':'本机音色试听','items':[
        {'kind':'tool','tool':'bt_preview_chinese','title':'试听中文 BT'},
        {'kind':'tool','tool':'bt_preview_english','title':'试听英文 BT（实验）'}]})
    state=voice_state.read()
    selected=voice_state.target(conversation_settings.read())
    draft=state['text'] if selected and state['target']==selected['id'] else ''
    result['schema']['properties'].update({
        'voice_draft':{'type':'string','title':'语音转写草稿','description':'可编辑后点击发送草稿；不会自动进入任何其他会话。'},
        'voice_status':{'type':'string','title':'麦克风状态','enum':[state['status']]}})
    result['values'].update(voice_draft=draft,voice_status=state['status'])
    result['layout'].append({'kind':'group','title':'本机语音输入','items':[
        {'kind':'property','property':'microphone_enabled'},
        {'kind':'property','property':'voice_status'},
        {'kind':'property','property':'voice_draft'},
        {'kind':'tool','tool':'bt_send_voice_draft','title':'发送草稿到选中会话'},
        {'kind':'tool','tool':'bt_refresh_voice','title':'读取最新转写'},
        {'kind':'tool','tool':'bt_stop_voice','title':'停止收音和播报'}]})
    try:
        rows=await settings_rows(ctx)
        fields,values,layout=conversation_settings.describe(rows)
        result['schema']['properties']={**result['schema']['properties'],**fields}
        result['values'].update(values);result['layout'].extend(layout)
    except Exception:
        # Keep global preferences usable when Codex changes its connector.
        # Do not fall back to reading private databases or conversation files.
        result['schema']['properties']['conversation_status']={'type':'string','title':'会话连接状态','enum':['会话列表暂不可用；已有独立配置已保留']}
        result['values']['conversation_status']='会话列表暂不可用；已有独立配置已保留'
    return localize(result,bt_settings.read()['interface_language'])


@server.tool(title='BT 原生设置',description='读取通用设置及会话标题列表。不读取聊天正文，不打开网页。',
    annotations=READ_HINTS,meta={'ui':{'visibility':['app']}})
async def bt_settings_read(ctx:Context)->SettingsReadResult:
    return await settings_description(ctx)


@server.tool(title='更新 BT 通用设置',description='供 Codex 原生插件设置页保存通用默认值；不改变任何 Codex 模型、权限或工作目录。',
    annotations=NETWORK_HINTS,meta={'ui':{'visibility':['app']}})
async def bt_settings_update(set:dict,ctx:Context)->SettingsUpdateResult:
    set=normalize_changes(set)
    if 'voice_draft' in set:
        if len(set)!=1 or not isinstance(set['voice_draft'],str):raise ValueError('草稿必须是文字')
        selected=voice_state.target(conversation_settings.read())
        if not selected:raise ValueError('请先选择并启用目标会话')
        voice_state.write(target=selected['id'],text=set['voice_draft'])
        return {'values':(await settings_description(ctx))['values']}
    provider_changes={k:v for k,v in set.items() if k in provider_settings.FIELDS}
    if provider_changes:
        if len(provider_changes)!=len(set):raise ValueError('连接配置与会话设置请分别保存')
        provider_settings.update(provider_changes)
        await ctx.session.send_tool_list_changed()
        return {'values':(await settings_description(ctx))['values']}
    global_changes={k:v for k,v in set.items() if k in bt_settings.DEFAULTS}
    local_changes={k:v for k,v in set.items() if k not in bt_settings.DEFAULTS}
    # The host sends one changed native control at a time. Reject mixed writes.
    if global_changes and local_changes:raise ValueError('通用设置与会话设置请分别保存')
    if local_changes:
        conversation_settings.update(local_changes,await settings_rows(ctx))
        if any(k.endswith('__enabled') and v is True for k,v in local_changes.items()):
            import asyncio
            await asyncio.to_thread(restore_enabled_service)
    else:
        bt_settings.update(global_changes)
        if 'interface_language' in global_changes:
            await ctx.session.send_tool_list_changed()
        if global_changes.get('microphone_enabled'):
            await asyncio.to_thread(restore_enabled_service)
    return {'values':(await settings_description(ctx))['values']}


@server.tool(title='测试当前连接',description='测试本机保存的当前摘要服务连接；不会读取聊天正文。',
    annotations=NETWORK_HINTS,meta={'ui':{'visibility':['app']}})
async def bt_test_connection(ctx:Context)->str:
    profile=provider_settings.active()
    connection_feedback.write(profile,'running')
    await ctx.session.send_tool_list_changed()
    code=await connection_feedback.run(profile)
    await ctx.session.send_tool_list_changed()
    return connection_feedback.message(code,bt_settings.read()['interface_language'])


@server.tool(title='发送语音草稿',description='只在用户点击时发送本机转写草稿到明确选中的已启用会话。',annotations=NETWORK_HINTS,meta={'ui':{'visibility':['app']}})
def bt_send_voice_draft(ctx:Context)->str:
    caller_context(ctx)
    result=action_call('send_draft',{})
    return result['message']


@server.tool(title='读取最新转写',description='读取当前本机语音转写，不发送消息。',annotations=READ_HINTS,meta={'ui':{'visibility':['app']}})
def bt_refresh_voice()->str:
    state=voice_state.read()
    return state['status']+'\n'+state['text']


@server.tool(title='停止语音',description='关闭本机收音并停止声音，不停止 Codex 任务。',annotations=NETWORK_HINTS,meta={'ui':{'visibility':['app']}})
def bt_stop_voice()->str:
    bt_settings.update({'microphone_enabled':False})
    token_file=ROOT/'runtime/companion/token'
    if token_file.exists():
        try:
            httpx.post('http://127.0.0.1:12396/api/action',headers={'X-BT-Token':token_file.read_text(encoding='utf8')},
                json={'action':'stop_voice','args':{}},timeout=3).raise_for_status()
        except httpx.HTTPError:return '已关闭收音设置；后台暂不可达，未能确认声音停止。'
    return '麦克风已关闭，已停止播报；Codex 任务继续。'


def caller_context(ctx):
    meta=ctx.request_context.meta or {}
    for key in ['openai/threadId','openai/thread_id','codexThreadId','threadId','thread_id']:
        if isinstance(meta.get(key),str):
            os.environ['CODEX_THREAD_ID']=meta[key]
            break


def ensure_service(require_desktop=True):
    try:
        r=httpx.get('http://127.0.0.1:12396/health',timeout=2)
        if r.status_code==200:
            if not require_desktop:return
            pipe=os.getenv('CODEX_APP_TOOLS_PIPE_PATH')
            if not pipe or (r.json().get('desktopConnected') and r.json().get('contextId')==hashlib.sha256(pipe.encode()).hexdigest()):return
            subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'Stop-BT.ps1'),'-Services','bt-panel'],
                capture_output=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),timeout=30)
    except httpx.HTTPError:pass
    env=os.environ.copy();env['BT_NO_BROWSER']='1'
    launch=subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'scripts/start_companion_detached.ps1')],
        cwd=str(ROOT),env=env,capture_output=True,text=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),timeout=30)
    if launch.returncode:
        raise RuntimeError('Windows 未能启动 BT 服务：'+launch.stderr)
    for _ in range(100):
        time.sleep(1)
        try:
            check=httpx.get('http://127.0.0.1:12396/health',timeout=2)
            if check.is_success and (not require_desktop or check.json().get('desktopConnected')):return
        except httpx.HTTPError:pass
    raise RuntimeError('BT 服务尚未启动，请查看 Level 2/runtime/plugin-start.log')


def action_call(action,args):
    ensure_service(require_desktop=action not in {'preview_voice','speak_text','audio','state','stop_voice'})
    token=(ROOT/'runtime/companion/token').read_text(encoding='utf-8')
    r=httpx.post('http://127.0.0.1:12396/api/action',headers={'X-BT-Token':token},
        json={'action':action,'args':args},timeout=100)
    if not r.is_success:raise ValueError(r.text)
    return r.json()


@server.tool(title='试听中文 BT',description='播放固定的本机中文音色样例，不读取聊天、不调用摘要服务。',annotations=NETWORK_HINTS,meta={'ui':{'visibility':['app']}})
def bt_preview_chinese()->str:
    action_call('preview_voice',{'language':'zh'})
    return '中文 BT 试听已完成。'


@server.tool(title='试听英文 BT',description='试听 DJMalachite 的独立英文 BT 社区模型，不使用中文参考或云 TTS。',annotations=NETWORK_HINTS,meta={'ui':{'visibility':['app']}})
def bt_preview_english()->str:
    action_call('preview_voice',{'language':'en'})
    return '英文 BT 实验音色试听已完成；相似度需要人耳判断。'


@server.tool(description='说明 BT 原生设置入口。不打开任何网页或内嵌面板。',
    annotations=READ_HINTS)
def open_bt(ctx:Context)->dict:
    return {'message':'请在 Codex 插件 → BT-7274 语音伙伴 → 管理中选择会话，设置独立配置。不打开网页。'}


@server.tool(description='BT面板内部操作。发送消息必须来自用户对目标会话的明确输入；不得自行发消息或创建任务。',
    annotations=NETWORK_HINTS,meta={'ui':{'visibility':['app']}})
def bt_action(action:str,args:dict,ctx:Context)->dict:
    caller_context(ctx)
    return action_call(action,args)


@server.tool(description='用户要求时，让 BT 简短播报指定文字。只影响语音，不修改 Codex 原文。',annotations=NETWORK_HINTS)
def speak(text:str,ctx:Context,bt_style:bool=True)->dict:
    caller_context(ctx)
    return action_call('speak_text',{'text':text,'btStyle':bt_style})


def restore_enabled_service():
    enabled=[s for s in conversation_settings.read()['conversations'].values() if s.get('enabled')]
    if not enabled or not os.getenv('CODEX_APP_TOOLS_PIPE_PATH'):return
    # A global settings discovery may have no current-chat ID. The explicitly
    # enabled saved chat is sufficient context; do not create a chat or agent.
    if not (os.getenv('CODEX_THREAD_ID') or os.getenv('CODEX_SESSION_ID')):
        os.environ['CODEX_THREAD_ID']=enabled[0]['id']
    lock=ROOT/'runtime/service-recovery.lock'
    lock.parent.mkdir(parents=True,exist_ok=True)
    with FileLock(str(lock),timeout=30):
        ensure_service()


async def maintain_service():
    while True:
        try:await asyncio.to_thread(restore_enabled_service)
        except Exception as exc:
            # Keep initialization independent of service recovery. Log no tokens,
            # pipe paths, or conversation text.
            log=ROOT/'runtime/service-recovery.log'
            log.parent.mkdir(parents=True,exist_ok=True)
            log.write_text(type(exc).__name__,encoding='utf8')
        await asyncio.sleep(15)


async def run_stdio():
    # Older desktop MCP connections use experimental; modern discovery uses
    # extensions. Advertise the same native settings capability in both eras.
    from mcp.server.stdio import stdio_server
    from mcp.server.lowlevel import NotificationOptions
    recovery=asyncio.create_task(maintain_service())
    try:
        async with stdio_server() as (read_stream,write_stream):
            await server._lowlevel_server.run(read_stream,write_stream,
                server._lowlevel_server.create_initialization_options(
                    notification_options=NotificationOptions(tools_changed=True),
                    experimental_capabilities={'openai/settings':server._lowlevel_server.extensions['openai/settings']}))
    finally:
        recovery.cancel()
        try:await recovery
        except asyncio.CancelledError:pass


if __name__=='__main__':
    import anyio
    anyio.run(run_stdio)
