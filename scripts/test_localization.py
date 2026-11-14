# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

import unittest
import bt_settings
import provider_settings
import conversation_settings
from localization import localize,normalize_changes

class LocalizationTests(unittest.TestCase):
    def definition(self):
        data=bt_settings.describe();connection=provider_settings.describe()
        data['schema']['properties']={**data['schema']['properties'],**connection['schema']['properties']}
        data['values'].update(connection['values']);data['layout']+=connection['layout']
        rows=[{'id':'test','hostId':'local','title':'我的会话','pinned':True}]
        fields,values,layout=conversation_settings.describe(rows,{'selected':'','conversations':{}})
        data['schema']['properties'].update(fields);data['values'].update(values);data['layout']+=layout
        return data

    def test_english_labels_keep_schema_and_values_consistent(self):
        data=localize(self.definition(),'English')
        for name,field in data['schema']['properties'].items():
            if 'enum' in field:self.assertIn(data['values'][name],field['enum'],name)
        self.assertEqual(data['schema']['properties']['api_key']['title'],'API key')
        self.assertEqual(data['layout'][-1]['title'],'我的会话')

    def test_choice_roundtrip_and_api_text_not_translated(self):
        data=localize(self.definition(),'English')
        mapped=normalize_changes(data['values'])
        self.assertEqual(mapped['default_mode'],bt_settings.read()['default_mode'])
        self.assertNotIn('speech_language',mapped)
        self.assertEqual(mapped['interface_language'],'简体中文')
        self.assertEqual(normalize_changes({'api_key':'Default','base_url':'https://example.test','model':'On'}),{'api_key':'Default','base_url':'https://example.test','model':'On'})

    def test_all_languages_roundtrip_without_changing_user_text(self):
        original=self.definition()
        for language in ('简体中文','English','日本語'):
            data=localize(original,language)
            for name,field in data['schema']['properties'].items():
                if 'enum' in field:self.assertIn(data['values'][name],field['enum'],(language,name))
            normalized=normalize_changes(data['values'])
            self.assertEqual(normalized['speech_voice'],original['values']['speech_voice'])
            self.assertEqual(normalized['selected_conversation'],original['values']['selected_conversation'])
            self.assertEqual(data['layout'][-1]['title'],'我的会话')
        self.assertEqual(localize(original,'日本語')['schema']['properties']['api_key']['title'],'API キー')
        self.assertEqual(normalize_changes({'api_key':'共通設定','model':'英語'}),{'api_key':'共通設定','model':'英語'})

if __name__=='__main__':unittest.main()
