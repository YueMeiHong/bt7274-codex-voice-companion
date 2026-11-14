# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

"""Plugin-wide preferences. Conversation overrides live separately."""
import json
from pathlib import Path
import threading
from filelock import FileLock

PATH=Path(__file__).resolve().parents[1]/'config/companion-settings.json'
LOCK=threading.Lock()
DEFAULTS={'bt_style':False,'summary_length':'short','volume':100,'default_mode':'reply','auto_send':False,'microphone_enabled':False,'speech_voice':'自动（中英）','interface_language':'简体中文'}
FIELDS={
    'interface_language':{'type':'string','title':'设置界面语言 / Settings language','enum':['简体中文','English','日本語'],'description':'只改变原生设置的显示文字，不改变语音或 Codex 原会话语言。'},
    'speech_voice':{'type':'string','title':'语音语言','enum':['自动（中英）','中文','英文'],'description':'AI 合成语音，非官方录音。中文：MiDd1Eye / Bert-VITS2；英文：DJMalachite / Piper。摘要语言随声音选择，界面语言独立。'},
    'microphone_enabled':{'type':'boolean','title':'开启本机麦克风','description':'仅向下方明确选择、已启用且用途为双向语音的会话发送。关闭自动发送时，转写保留为草稿。'},
    'bt_style':{'type':'boolean','title':'简短 BT 风格播报','description':'配置摘要服务后开启；关闭时直接播报简短原文。仅处理最终回答，不改变原回答或参与执行。'},
    'summary_length':{'type':'string','title':'播报长度','enum':['short','normal'],'description':'short：通常1至2句；normal：允许稍详细的口头汇报。'},
    'volume':{'type':'integer','title':'默认播报音量（%）','minimum':0,'maximum':100},
    'default_mode':{'type':'string','title':'新启用会话的默认用途','enum':['talk','reply','notify'],'description':'talk：双向语音；reply：只播报回复；notify：只通知结果。会话可单独覆盖。'},
    'auto_send':{'type':'boolean','title':'默认自动发送语音转写','description':'关闭后先把转写放入输入框，确认或修改后再发送。'},
}


def validate(changes):
    if not isinstance(changes,dict) or set(changes)-set(DEFAULTS):raise ValueError('包含未知的 BT 通用设置')
    changes=dict(changes)
    if 'speech_voice' in changes:
        changes['speech_voice']={'中文 BT':'中文','英文 BT（实验）':'英文','英文 BT':'英文'}.get(changes['speech_voice'],changes['speech_voice'])
    for key,value in changes.items():
        field=FIELDS[key]
        if field['type']=='boolean' and type(value) is not bool:raise ValueError(key+' 必须为开关值')
        if field['type']=='integer' and (type(value) is not int or not 0<=value<=100):raise ValueError('音量必须是0至100的整数')
        if 'enum' in field and value not in field['enum']:raise ValueError(key+' 取值无效')
    return changes


def read(path=None):
    path=Path(path) if path else PATH
    values=dict(DEFAULTS)
    if path.exists():values.update(validate(json.loads(path.read_text(encoding='utf-8'))))
    return values


def update(changes,path=None):
    changes=validate(changes)
    path=Path(path) if path else PATH
    path.parent.mkdir(parents=True,exist_ok=True)
    with LOCK,FileLock(str(path)+'.lock'):
        values=read(path);values.update(changes)
        temp=path.with_suffix('.tmp')
        temp.write_text(json.dumps(values,ensure_ascii=False,indent=2),encoding='utf-8')
        temp.replace(path)
    return values


def effective(subscription,values):
    result=dict(subscription)
    result['mode']=result.get('modeOverride') or values['default_mode']
    result['btStyle']=values['bt_style'] if result.get('btStyleOverride') is None else result['btStyleOverride']
    return result


def describe():
    return {'schema':{'type':'object','properties':FIELDS},'values':read(),'layout':[
        {'kind':'group','title':'设置界面 / Settings','items':[{'kind':'property','property':'interface_language'}]},
        {'kind':'group','title':'BT 播报（所有会话的默认值）','items':[{'kind':'property','property':k} for k in ['bt_style','summary_length','volume','speech_voice']]},
        {'kind':'group','title':'会话默认行为','items':[{'kind':'property','property':k} for k in ['default_mode','auto_send']]},
    ]}
