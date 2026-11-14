# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

"""Refuse modified model code, configuration and weights before importing them."""
import hashlib
import json
from pathlib import Path

MANIFEST = Path(__file__).resolve().parents[1] / 'config/model-integrity.json'


def verify_model(category, directory, manifest=MANIFEST):
    root = Path(directory).resolve()
    entries = json.loads(Path(manifest).read_text(encoding='utf8'))[category]
    if not entries:
        raise RuntimeError('Model integrity manifest is empty')
    for name, expected in entries.items():
        target = (root / name).resolve()
        if not target.is_relative_to(root) or not target.is_file():
            raise RuntimeError('Model asset missing or outside model directory: ' + name)
        with target.open('rb') as stream:
            actual = hashlib.file_digest(stream, 'sha256').hexdigest()
        if actual != expected:
            raise RuntimeError('Model integrity check failed: ' + name)
    # Prevent unlisted Python modules and local configuration overriding trusted files.
    if category == 'chinese_bt':
        for pattern in ('*.py', '*.json', '*.pth', '*.bin'):
            for path in root.rglob(pattern):
                if '.git' not in path.parts and path.relative_to(root).as_posix() not in entries:
                    raise RuntimeError('Unlisted model code/configuration: ' + path.relative_to(root).as_posix())
    return True
