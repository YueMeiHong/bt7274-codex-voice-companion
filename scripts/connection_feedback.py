# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

"""Visible native connection-test feedback, shared across MCP processes."""
import hashlib
import json
from datetime import datetime
from pathlib import Path
from filelock import FileLock
from provider_client import test_connection,ProviderError

PATH=Path(__file__).resolve().parents[1]/'runtime/connection-test.json'
MESSAGES={
 'idle':('尚未测试当前连接','Current connection not tested','現在の接続は未テストです'),
 'running':('正在测试连接…','Testing connection…','接続をテスト中…'),
 'success':('连接成功，当前模型已返回测试回复。','Connected: the current model replied.','接続成功：現在のモデルから応答がありました。'),
 'unexpected':('测试失败：服务暂不可用，请稍后重试。','Test failed: service unavailable; please retry.','テスト失敗：サービスを利用できません。再試行してください。'),
 '请先填写模型名称':('请先填写模型名称','Enter a model ID first.','モデル ID を入力してください。'),
 '请先填写当前服务商的 API Key':('请先填写当前服务商的 API Key','Enter the current provider’s API key first.','現在のプロバイダーの API キーを入力してください。'),
 '认证失败：请检查当前服务商的 API Key 或权限':('认证失败：请检查当前服务商的 API Key 或权限','Authentication failed: check the API key and permissions.','認証失敗：API キーと権限を確認してください。'),
 '未找到接口或模型：请检查 API 地址与模型名称':('未找到接口或模型：请检查 API 地址与模型名称','Endpoint or model not found: check the URL and model ID.','API またはモデルが見つかりません。URL とモデル ID を確認してください。'),
 '请求受限：请检查额度或稍后重试':('请求受限：请检查额度或稍后重试','Rate or quota limit: check usage or retry later.','利用制限：残高を確認するか、後で再試行してください。'),
 '连接超时：请检查服务地址和本机网络':('连接超时：请检查服务地址和本机网络','Connection timed out: check the URL and network.','接続がタイムアウトしました。URL とネットワークを確認してください。'),
 '无法连接：请检查服务地址，使用 Ollama 时确认它已启动':('无法连接：请检查服务地址，使用 Ollama 时确认它已启动','Cannot connect: check the URL; make sure Ollama is running if selected.','接続できません。URL を確認し、Ollama を選択した場合は起動してください。'),
 '服务返回格式不兼容：需要 OpenAI 兼容聊天接口':('服务返回格式不兼容：需要 OpenAI 兼容聊天接口','Incompatible response: an OpenAI-compatible chat endpoint is required.','応答形式が非互換です。OpenAI 互換のチャット API が必要です。')}

def fingerprint(profile):
    return hashlib.sha256(json.dumps(profile,sort_keys=True).encode()).hexdigest()

def _record(profile,path=None):
    p=Path(path) if path else PATH
    try:data=json.loads(p.read_text(encoding='utf8'))
    except (OSError,ValueError):return {}
    return data if isinstance(data,dict) and data.get('fingerprint')==fingerprint(profile) else {}

def read(profile,path=None):
    return _record(profile,path).get('code','idle')

def write(profile,code,path=None):
    p=Path(path) if path else PATH;p.parent.mkdir(parents=True,exist_ok=True)
    with FileLock(str(p)+'.lock'):
        temp=p.with_suffix('.tmp')
        record={'fingerprint':fingerprint(profile),'code':code,'checked_at':datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        temp.write_text(json.dumps(record),encoding='utf8')
        temp.replace(p)

def message(code,language):
    return MESSAGES.get(code,MESSAGES['unexpected'])[{'English':1,'日本語':2}.get(language,0)]

async def run(profile,path=None):
    write(profile,'running',path)
    try:
        await test_connection(profile);code='success'
    except ProviderError as exc:code=str(exc) if str(exc) in MESSAGES else 'unexpected'
    except Exception:code='unexpected'
    write(profile,code,path)
    return code

def display_result(profile,language,path=None):
    record=_record(profile,path)
    code=record.get('code','idle')
    result=message(code,language)
    if code not in {'idle','running','success','unexpected'}:
        result={'English':'Test failed: ','日本語':'テスト失敗：'}.get(language,'测试失败：')+result
    checked_at=record.get('checked_at')
    return f'{checked_at} · {result}' if checked_at and code!='running' else result
