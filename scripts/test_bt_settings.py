# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

import tempfile
from pathlib import Path
import unittest
import bt_settings


class SettingsTests(unittest.TestCase):
    def test_partial_update_persists_without_erasing_other_defaults(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'settings.json'
            self.assertFalse(p.exists())
            self.assertEqual(bt_settings.read(p),bt_settings.DEFAULTS)
            self.assertFalse(p.exists(),'Reading native settings must not write files')
            bt_settings.update({'volume':42},p)
            self.assertEqual(bt_settings.read(p),{**bt_settings.DEFAULTS,'volume':42})

    def test_codex_configuration_cannot_be_written_as_bt_preference(self):
        for changes in [{'model':'other'},{'approval_policy':'never'},{'cwd':'C:/'}]:
            with self.assertRaises(ValueError):bt_settings.validate(changes)

    def test_invalid_values_are_rejected(self):
        for changes in [{'volume':101},{'volume':True},{'bt_style':'true'},{'default_mode':'unknown'}]:
            with self.assertRaises(ValueError):bt_settings.validate(changes)

    def test_explicit_conversation_choice_wins_over_global_default(self):
        prefs={**bt_settings.DEFAULTS,'default_mode':'notify','bt_style':False}
        self.assertEqual(bt_settings.effective({'modeOverride':'reply','btStyleOverride':True},prefs)['mode'],'reply')
        inherited=bt_settings.effective({'modeOverride':None,'btStyleOverride':None},prefs)
        self.assertEqual(inherited['mode'],'notify')
        self.assertFalse(inherited['btStyle'])


if __name__=='__main__':unittest.main()
