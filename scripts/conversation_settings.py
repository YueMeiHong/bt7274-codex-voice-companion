# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

"""Persistent BT overrides, keyed by host and conversation ID; no chat bodies."""
import hashlib
import json
from pathlib import Path
from filelock import FileLock
import bt_settings

PATH = Path(__file__).resolve().parents[1]/'config/conversation-settings.json'
OVERRIDES = {'mode': ['inherit','talk','reply','notify'],
             'bt_style': ['inherit','on','off'],
             'summary_length': ['inherit','short','normal'],
             'auto_send': ['inherit','on','off']}
DEFAULT = {'enabled':False, 'mode':'inherit', 'bt_style':'inherit',
           'summary_length':'inherit', 'volume':-1, 'auto_send':'inherit'}
LABELS={'mode':{'inherit':'通用','talk':'双向语音','reply':'只播报回复','notify':'只通知结果'},
        'summary_length':{'inherit':'通用','short':'简短','normal':'正常'},
        'bt_style':{'inherit':'通用','on':'开启','off':'关闭'},
        'auto_send':{'inherit':'通用','on':'开启','off':'关闭'}}

def inherited(item,field):
    return item.get(field,DEFAULT[field])==(-1 if field=='volume' else 'inherit')

def concrete(field,defaults):
    if field=='mode':return defaults['default_mode']
    if field in {'bt_style','auto_send'}:return 'on' if defaults[field] else 'off'
    return defaults[field]

def key(row):
    return hashlib.sha256(json.dumps([row.get('hostId') or 'local',row['id']]).encode()).hexdigest()[:24]

def read(path=None):
    p=Path(path) if path else PATH
    return json.loads(p.read_text(encoding='utf8')) if p.exists() else {'selected':'','conversations':{}}

def update(changes, rows, path=None):
    # Native selects show Chinese labels; persisted values remain compatible.
    changes=dict(changes)
    for name,value in changes.items():
        field=name.split('__')[-1]
        if field=='volume' and type(value) is str:
            if value=='通用':value=-1
            elif value.endswith('%') and value[:-1].isdigit():value=int(value[:-1])
        changes[name]=next((k for k,v in LABELS.get(field,{}).items() if v==value),value)
    p=Path(path) if path else PATH
    indexed={key(r):r for r in rows}
    labels={label(r):key(r) for r in rows}
    # Validate the entire change before modifying any saved configuration.
    for name,value in changes.items():
        if name=='selected_conversation':
            if value not in labels: raise ValueError('会话列表已变化，请重新选择')
            continue
        parts=name.split('__')
        if len(parts)!=3 or parts[0]!='conversation' or parts[1] not in indexed:
            raise ValueError('未知或已不在列表中的会话')
        field=parts[2]
        if field.endswith('_inherit'):
            valid=field[:-8] in OVERRIDES or field[:-8]=='volume'
            valid=valid and type(value) is bool
        elif field=='volume_source':valid=value in ['通用','自定义']
        elif field=='enabled': valid=type(value) is bool
        elif field=='volume': valid=type(value) is int and -1<=value<=100
        elif field in {'bt_style','auto_send'}:valid=type(value) is bool or value in OVERRIDES[field]
        else: valid=field in OVERRIDES and (value in OVERRIDES[field] or value in LABELS.get(field,{}).values())
        if not valid: raise ValueError('无效的会话设置')
    p.parent.mkdir(parents=True,exist_ok=True)
    with FileLock(str(p)+'.lock'):
        data=read(p)
        for name,value in changes.items():
            if name=='selected_conversation': data['selected']=labels[value];continue
            _,ident,field=name.split('__')
            row=indexed[ident]
            # The native select initially displays the first row without
            # emitting a change. Persist that visible target on the first edit.
            # A stale page must not replace an already valid selected target.
            if data.get('selected') not in indexed:data['selected']=ident
            item=data['conversations'].setdefault(ident, {'id':row['id'],'hostId':row.get('hostId') or 'local',**DEFAULT})
            if field=='volume_source':
                if value=='通用':item['volume']=-1
                elif item['volume']==-1:item['volume']=bt_settings.read()['volume']
            elif field.endswith('_inherit'):
                target=field[:-8]
                if value:item[target]=-1 if target=='volume' else 'inherit'
                elif inherited(item,target):item[target]=concrete(target,bt_settings.read())
            elif field in {'bt_style','auto_send'} and type(value) is bool:
                item[field]='on' if value else 'off'
            else:
                item[field]=next((k for k,v in LABELS.get(field,{}).items() if v==value),value)
        temp=p.with_suffix('.tmp');temp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8');temp.replace(p)
    return data

def label(row):
    return ('置顶 · ' if row.get('pinned') else '最近 · ')+(row.get('title') or '未命名会话')+' ['+key(row)[:8]+']'

def preferences(item, defaults=None):
    values=dict(defaults or bt_settings.read())
    for field in ['bt_style','auto_send']:
        if item.get(field,'inherit')!='inherit':values[field]=item[field]=='on'
    if item.get('summary_length','inherit')!='inherit':values['summary_length']=item['summary_length']
    if item.get('volume',-1)>=0:values['volume']=item['volume']
    values['mode']=values['default_mode'] if item.get('mode','inherit')=='inherit' else item['mode']
    return values

def describe(rows, data=None):
    data=data or read()
    indexed={key(r):r for r in rows}
    if not rows:return {},{},[]
    selected=data.get('selected')
    if selected not in indexed:selected=next(iter(indexed))
    row=indexed[selected]
    fields={'selected_conversation':{'type':'string','title':'选择会话（置顶在前，其余按最近顺序）','enum':[label(r) for r in rows],
        'description':'仅列出标题与会话标识，不读取聊天正文。选择后下方显示该会话的独立设置。'}}
    values={'selected_conversation':label(row)}
    item={**DEFAULT,**data['conversations'].get(selected,{})}
    definitions={
        'enabled':{'type':'boolean','title':'为此会话启用 BT','description':'只影响此会话。配置自动保存；重启后保留。'},
        'mode':{'type':'string','title':'此会话用途','enum':list(LABELS['mode'].values()),'description':'通用：跟随通用用途；其他选项仅对此会话生效。'},
        'bt_style':{'type':'string','title':'此会话 BT 风格摘要','enum':list(LABELS['bt_style'].values()),'description':'通用：跟随通用设置；开启或关闭：此会话使用指定值。'},
        'summary_length':{'type':'string','title':'此会话播报长度','enum':list(LABELS['summary_length'].values()),'description':'选择此会话的具体播报长度。'},
        'volume_source':{'type':'string','title':'此会话音量设置','enum':['通用','自定义'],'description':'通用：跟随默认音量；自定义：使用此会话的独立音量。'},
        'volume':{'type':'integer','title':'此会话音量（%）','minimum':0,'maximum':100,'multipleOf':1,'description':'可直接输入或用上下箭头微调；0 为静音。修改数字后自动使用自定义音量。'},
        'auto_send':{'type':'string','title':'此会话自动发送转写','enum':list(LABELS['auto_send'].values()),'description':'通用：跟随通用设置；开启：自动发送；关闭：先确认转写。'},
    }
    keys=[]
    for field,definition in definitions.items():
        name='conversation__'+selected+'__'+field
        fields[name]=definition
        if field=='volume_source':value='通用' if item['volume']==-1 else '自定义'
        elif field=='volume':value=bt_settings.read()['volume'] if item['volume']==-1 else item['volume']
        else:value=item[field]
        values[name]=LABELS.get(field,{}).get(value,value)
        keys.append(name)
    return fields,values,[{'kind':'group','title':'会话列表','items':[{'kind':'property','property':'selected_conversation'}]},
        {'kind':'group','title':row.get('title') or '未命名会话','items':[{'kind':'property','property':k} for k in keys]}]
