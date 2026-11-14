# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

"""Local draft/state for native microphone controls; no webpage required."""
import json
from pathlib import Path
import uuid
from filelock import FileLock

PATH=Path(__file__).resolve().parents[1]/'runtime/voice-state.json'

def read(path=None):
    p=Path(path) if path else PATH
    return json.loads(p.read_text(encoding='utf8')) if p.exists() else {'target':'','text':'','status':'麦克风未开启','id':''}

def write(path=None,**changes):
    p=Path(path) if path else PATH;p.parent.mkdir(parents=True,exist_ok=True)
    with FileLock(str(p)+'.lock'):
        data=read(p);data.update(changes)
        if 'text' not in changes and data==read(p):return data
        if 'text' in changes:data['id']=uuid.uuid4().hex
        tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False),encoding='utf8');tmp.replace(p)
    return data

def target(configuration):
    selected=configuration.get('selected')
    item=configuration.get('conversations',{}).get(selected)
    if not item or not item.get('enabled'):return None
    return item
