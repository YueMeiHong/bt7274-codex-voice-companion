# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

"""Portable installation paths and deterministic local preflight checks."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
CORE_REQUIREMENTS=[
    'fastapi>=0.115,<1','uvicorn>=0.33,<1','httpx>=0.28,<1','mcp==2.3.0',
    'filelock>=3,<5','typing-extensions>=4.12','numpy>=1.26.4,<2',
    'scipy>=1.14,<2','sherpa-onnx>=1.10.39','soundfile>=0.12,<1','sounddevice>=0.5,<1','cn2an==0.5.23','piper-tts==1.8.0',
]
VOICE_REQUIREMENTS=[
    'torch==2.7.1','transformers==4.57.6','jieba==0.42.1','pypinyin==0.53.0',
    'librosa==0.10.2.post1','Unidecode==1.3.8',
]
CORE_MODULES=['fastapi','uvicorn','httpx','mcp','filelock','numpy','scipy','sherpa_onnx','soundfile','sounddevice','cn2an']
VOICE_MODULES=['torch','transformers','jieba','pypinyin','librosa']
ASR_NAME='sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17'

class RuntimeDependencyError(RuntimeError):
    pass

def project_root(root=None):
    return Path(root).resolve() if root is not None else ROOT

def settings(root=None):
    p=project_root(root)/'config/runtime-paths.json'
    if not p.exists():return {}
    data=json.loads(p.read_text(encoding='utf-8-sig'))
    if not isinstance(data,dict) or set(data)-{'python','tts_directory','asr_directory'}:
        raise RuntimeDependencyError('config/runtime-paths.json contains unknown settings')
    return data

def _path(value,root):
    path=Path(value)
    return path if path.is_absolute() else root/path

def python_path(root=None):
    root=project_root(root);configured=settings(root).get('python')
    if configured:return _path(configured,root)
    relative='Scripts/python.exe' if sys.platform=='win32' else 'bin/python'
    independent=root/'.venv-local'/relative
    if independent.exists():return independent
    return root/'.venv'/relative

def tts_directory(root=None):
    root=project_root(root)
    return _path(settings(root).get('tts_directory','vendor/BT7274-Bert-VITS2'),root)

def asr_directory(root=None):
    root=project_root(root)
    return _path(settings(root).get('asr_directory','vendor/Open-LLM-VTuber-main/models/'+ASR_NAME),root)

def missing_assets(root=None):
    tts=tts_directory(root);asr=asr_directory(root)
    required={
        'BT source':tts/'models.py',
        'BT configuration':tts/'configs/config.json',
        'BT voice weights':tts/'logs/bt/bt.pth',
        'BT BERT weights':tts/'bert/chinese-roberta-wwm-ext-large/pytorch_model.bin',
        'ASR model':asr/'model.int8.onnx',
        'ASR tokens':asr/'tokens.txt',
    }
    return {name:str(path) for name,path in required.items() if not path.is_file()}

def check(root=None,check_modules=True):
    root=project_root(root)
    modules=CORE_MODULES+VOICE_MODULES
    missing=[]
    if check_modules:
        for module in modules:
            try:exists=importlib.util.find_spec(module) is not None
            except (ImportError,ModuleNotFoundError,ValueError):exists=False
            if not exists:missing.append(module)
    return {'root':str(root),'python':str(python_path(root)),
        'python_exists':python_path(root).is_file(),'missing_modules':missing,
        'missing_assets':missing_assets(root),'modules_checked':check_modules,
        'platform_supported':sys.platform=='win32'}

def require_runtime(root=None,check_modules=True,require_models=True):
    result=check(root,check_modules)
    errors=[]
    if not result['python_exists']:errors.append('Python environment missing; run Install-BT.ps1 -Install')
    if result['missing_modules']:errors.append('Missing Python packages: '+', '.join(result['missing_modules']))
    if require_models and result['missing_assets']:errors.append('Missing model files: '+', '.join(result['missing_assets']))
    if errors:raise RuntimeDependencyError('; '.join(errors))
    return result

def mcp_config(root=None):
    """Resolve installer-local paths; never embed an author's machine paths."""
    root=project_root(root)
    return {'mcpServers':{'bt_companion_level25':{
        'command':str(python_path(root)),
        'args':[str(root/'plugin/bt-companion/server.py')],
        'env_vars':['CODEX_THREAD_ID','CODEX_SESSION_ID','CODEX_APP_TOOLS_PIPE_PATH',
                    'CODEX_MCP_NODE_PATH','CODEX_BROWSER_USE_NODE_PATH','CODEX_ELECTRON_RESOURCES_PATH',
                    'CODEX_CLI_PATH','USERPROFILE','USERNAME','USERDOMAIN','LOCALAPPDATA','PATH'],
        'startup_timeout_sec':15,'tool_timeout_sec':180}}}

def configure(root=None,tts=None,asr=None,python=None):
    root=project_root(root);data=settings(root)
    for field,value in [('tts_directory',tts),('asr_directory',asr),('python',python)]:
        if value is not None:data[field]=str(value)
    p=root/'config/runtime-paths.json';p.parent.mkdir(parents=True,exist_ok=True)
    temporary=p.with_suffix('.tmp');temporary.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8');temporary.replace(p)
    return data

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root');parser.add_argument('--check',action='store_true')
    parser.add_argument('--no-modules',action='store_true')
    parser.add_argument('--strict',action='store_true')
    parser.add_argument('--require-models',action='store_true')
    parser.add_argument('--requirements',action='store_true')
    parser.add_argument('--configure',action='store_true')
    parser.add_argument('--python');parser.add_argument('--tts');parser.add_argument('--asr')
    parser.add_argument('--mcp-config',action='store_true')
    args=parser.parse_args()
    if args.requirements:
        print('\n'.join(CORE_REQUIREMENTS+VOICE_REQUIREMENTS));return
    if args.configure:configure(args.root,args.tts,args.asr,args.python)
    if args.mcp_config:print(json.dumps(mcp_config(args.root),ensure_ascii=False,indent=2));return
    result=check(args.root,not args.no_modules)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if args.strict or args.require_models:require_runtime(args.root,not args.no_modules,args.require_models)

if __name__=='__main__':main()
