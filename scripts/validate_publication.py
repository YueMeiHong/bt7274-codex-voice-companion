# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors
"""Validate the complete repo marketplace package without external services."""
import argparse
import json
from pathlib import Path
import re


def validate(root):
    root = Path(root).resolve()
    manifest = json.loads((root/'plugin.json').read_text(encoding='utf8'))
    compat = json.loads((root/'.codex-plugin/plugin.json').read_text(encoding='utf8'))
    assert re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', manifest['name'])
    assert re.fullmatch(r'\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?', manifest['version'])
    for key in ['name', 'version', 'license']:
        assert manifest[key] == compat[key], 'Compatibility manifest mismatch: '+key
    assert manifest['license'] == 'AGPL-3.0-only'
    assert 'GNU AFFERO GENERAL PUBLIC LICENSE' in (root/'LICENSE').read_text(encoding='utf8')
    interface = manifest['extensions']['com.openai']['interface']
    assert interface == compat['interface']
    assert 0 < len(interface['displayName']) <= 30
    assert 0 < len(interface['shortDescription']) <= 30
    assert interface['category'] == 'Productivity'
    assert len(interface['defaultPrompt']) <= 3
    review=manifest['extensions']['com.openai']['review']
    assert len(review['test_cases']['positive'])==5 and len(review['test_cases']['negative'])==3
    for case in review['test_cases']['positive']:
        assert all(isinstance(case[k],str) and case[k].strip() for k in ['description','prompt','tools_triggered','expected_behavior'])
    for case in review['test_cases']['negative']:
        assert all(isinstance(case[k],str) and case[k].strip() for k in ['description','prompt'])
    for key in ['logo', 'composerIcon']:
        path=(root/interface[key]).resolve()
        assert path.is_relative_to(root) and path.is_file(), 'Missing icon'
    onboarding=manifest['extensions']['com.openai']['onboardingSkill']
    assert (root/onboarding).is_file()
    catalog=json.loads((root/'.agents/plugins/marketplace.json').read_text(encoding='utf8'))
    entry=next(p for p in catalog['plugins'] if p['name']==manifest['name'])
    assert (root/entry['source']['path']).resolve()==root, 'Marketplace must include the complete runtime'
    config=json.loads((root/'mcp.json').read_text(encoding='utf8'))
    server=config['mcpServers']['bt_companion_level25']
    assert server['type']=='stdio' and server['command']=='powershell.exe'
    assert server['args'][-1]=='${PLUGIN_ROOT}/Launch-MCP.ps1'
    for path in ['Launch-MCP.ps1','Install-Portable.ps1','Install-BT.ps1','Setup-Models.ps1','Setup-English-BT.ps1',
                 'scripts/bootstrap_mcp.py','scripts/runtime_paths.py','scripts/local_security.py',
                 'plugin/bt-companion/server.py','config/model-integrity.json','THIRD_PARTY_NOTICES.md',
                 'SECURITY.md','CONTRIBUTING.md','CHANGELOG.md','.github/workflows/ci.yml']:
        assert (root/path).is_file(), 'Missing package file: '+path
    for path in ['README.md','README.en.md','README.ja.md']:
        assert 'AGPL' in (root/path).read_text(encoding='utf8')
    return {'passed':True,'name':manifest['name'],'version':manifest['version'],'license':manifest['license']}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    args=parser.parse_args()
    print(json.dumps(validate(args.root)))
