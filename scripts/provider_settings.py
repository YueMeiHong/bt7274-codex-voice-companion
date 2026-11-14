# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

"""Local, per-provider BT summary connections; independent of Level 1/.env."""
from copy import deepcopy
import json
from pathlib import Path
from urllib.parse import urlsplit

from filelock import FileLock

PATH = Path(__file__).resolve().parents[1]/'config/providers.json'
PRESETS = {
    'deepseek': {'base_url':'https://api.deepseek.com', 'api_key':'', 'model':'deepseek-flash'},
    'openai': {'base_url':'https://api.openai.com/v1', 'api_key':'', 'model':''},
    'custom': {'base_url':'http://localhost:8000/v1', 'api_key':'', 'model':''},
    'ollama': {'base_url':'http://localhost:11434/v1', 'api_key':'', 'model':''},
}
PROVIDER_LABELS = {'deepseek':'DeepSeek', 'openai':'OpenAI', 'custom':'自定义 OpenAI 兼容', 'ollama':'Ollama（本机）'}
LANGUAGE_LABELS = {'auto':'跟随原回复', 'zh':'简体中文', 'en':'English'}
FIELDS = {'provider','base_url','api_key','model','speech_language'}


def _choice(value, labels, title):
    if type(value) is not str:
        raise ValueError(title+'取值无效')
    if value in labels:
        return value
    for ident,label in labels.items():
        if value==label:
            return ident
    raise ValueError(title+'取值无效')


def _base_url(value):
    if type(value) is not str:
        raise ValueError('API 地址必须是文本')
    value=value.strip().rstrip('/')
    try:
        parsed=urlsplit(value)
        port=parsed.port  # Reject malformed and out-of-range ports.
    except ValueError as exc:
        raise ValueError('API 地址格式无效') from exc
    if (parsed.scheme not in {'http','https'} or not parsed.hostname
            or parsed.username is not None or parsed.password is not None
            or parsed.query or parsed.fragment or any(ch.isspace() for ch in value)):
        raise ValueError('API 地址须为 http/https 地址，不能包含账号密码、查询参数或片段')
    return value


def _connection(data):
    if not isinstance(data,dict) or set(data)-{'base_url','api_key','model'}:
        raise ValueError('模型连接配置无效')
    result={}
    if 'base_url' in data:
        result['base_url']=_base_url(data['base_url'])
    for field in ['api_key','model']:
        if field in data:
            if type(data[field]) is not str or any(ord(ch)<32 for ch in data[field]):
                raise ValueError(('API Key' if field=='api_key' else '模型名称')+'必须是文本')
            result[field]=data[field].strip()
    return result


def read(path=None):
    """Return all profiles; reading missing configuration does not create it."""
    data={'provider':'deepseek','speech_language':'auto','providers':deepcopy(PRESETS)}
    p=Path(path) if path else PATH
    if not p.exists():
        return data
    saved=json.loads(p.read_text(encoding='utf-8-sig'))
    if not isinstance(saved,dict) or set(saved)-{'provider','speech_language','providers'}:
        raise ValueError('本地模型配置格式无效')
    data['provider']=_choice(saved.get('provider','deepseek'),PROVIDER_LABELS,'服务商')
    data['speech_language']=_choice(saved.get('speech_language','auto'),LANGUAGE_LABELS,'摘要语言')
    profiles=saved.get('providers',{})
    if not isinstance(profiles,dict) or set(profiles)-set(PRESETS):
        raise ValueError('本地服务商列表无效')
    for ident,profile in profiles.items():
        data['providers'][ident].update(_connection(profile))
    return data


def active(path=None):
    """Return current connection with standard IDs for runtime API calls."""
    data=read(path)
    return {'provider':data['provider'], **data['providers'][data['provider']],
            'speech_language':data['speech_language']}


def update(changes,path=None):
    """Save changed native fields; return all profiles. No environment lookup."""
    if not isinstance(changes,dict) or set(changes)-FIELDS:
        raise ValueError('包含未知的模型设置')
    normalized={}
    if 'provider' in changes:
        normalized['provider']=_choice(changes['provider'],PROVIDER_LABELS,'服务商')
    if 'speech_language' in changes:
        normalized['speech_language']=_choice(changes['speech_language'],LANGUAGE_LABELS,'摘要语言')
    connection=_connection({k:v for k,v in changes.items() if k in {'base_url','api_key','model'}})
    # Codex native controls save one field at a time. Mixed provider/profile
    # changes are ambiguous and must never carry a key into a different host.
    if 'provider' in changes and connection:
        raise ValueError('先选择服务商，再填写该服务商的连接信息')
    p=Path(path) if path else PATH
    p.parent.mkdir(parents=True,exist_ok=True)
    with FileLock(str(p)+'.lock'):
        data=read(p)
        data.update(normalized)
        data['providers'][data['provider']].update(connection)
        temp=p.with_suffix('.tmp')
        temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        temp.replace(p)
    return data


def describe(path=None):
    """Return a Codex native structured-settings schema, values and layout."""
    current=active(path)
    fields={
        'provider': {'type':'string','title':'摘要模型服务商','enum':list(PROVIDER_LABELS.values()),
            'description':'选择连接后编辑下方详情。每个服务商的地址、Key 和模型分别保存在本机。'},
        'base_url': {'type':'string','title':'API 地址',
            'description':'填写服务根地址，不含 /chat/completions。Ollama 本机默认为 http://localhost:11434/v1。'},
        'api_key': {'type':'string','title':'API Key',
            'description':'保存在本机 Level 2.5 配置中。Ollama 本地连接通常可以留空；留空保存可清除当前 Key。'},
        'model': {'type':'string','title':'模型名称',
            'description':'填写服务商的模型 ID；Ollama 填写已安装模型的完整名称。'},
    }
    values={k:current[k] for k in ['provider','base_url','api_key','model']}
    values['provider']=PROVIDER_LABELS[current['provider']]
    return {'schema':{'type':'object','properties':fields},'values':values,'layout':[
        {'kind':'group','title':'摘要模型连接（保存在本机）','items':[
            {'kind':'property','property':k} for k in ['provider','base_url','api_key','model']]},
    ]}
