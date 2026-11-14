# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import conversation_settings as c

class ConversationSettingsTests(unittest.TestCase):
    def setUp(self):
        self.rows=[{'id':'a','hostId':'local','title':'同名','pinned':True},
                   {'id':'b','hostId':'local','title':'同名','pinned':False}]

    def test_selection_and_overrides_survive_reload_and_title_change(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'settings.json'
            ident=c.key(self.rows[1]);name='conversation__'+ident+'__volume'
            c.update({'selected_conversation':c.label(self.rows[1])},self.rows,path)
            c.update({name:23},self.rows,path)
            self.rows[1]['title']='改名'
            fields,values,_=c.describe(self.rows,c.read(path))
            self.assertEqual(values[name],23)
            self.assertIn('改名',values['selected_conversation'])
            self.assertEqual(values['conversation__'+ident+'__enabled'],False)
            self.assertNotIn(c.key(self.rows[0]),c.read(path)['conversations'])

    def test_old_page_cannot_write_to_new_selection(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'settings.json'
            c.update({'selected_conversation':c.label(self.rows[1])},self.rows,path)
            c.update({'conversation__'+c.key(self.rows[0])+'__volume':35},self.rows,path)
            saved=c.read(path)
            self.assertEqual(saved['conversations'][c.key(self.rows[0])]['volume'],35)
            self.assertNotIn(c.key(self.rows[1]),saved['conversations'])
            self.assertEqual(saved['selected'],c.key(self.rows[1]))

    def test_first_visible_conversation_is_selected_when_enabled(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'settings.json'
            ident=c.key(self.rows[0])
            c.update({'conversation__'+ident+'__enabled':True},self.rows,path)
            saved=c.read(path)
            self.assertEqual(saved['selected'],ident)
            self.assertTrue(saved['conversations'][ident]['enabled'])

    def test_invalid_update_is_atomic(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'settings.json'
            for field,value in [('volume',True),('enabled','true'),('mode','execute'),('cwd','D:/')]:
                with self.assertRaises(ValueError):c.update({'conversation__'+c.key(self.rows[0])+'__'+field:value},self.rows,path)
                self.assertFalse(path.exists())

    def test_native_list_order_and_host_identity(self):
        fields,_,_=c.describe(self.rows,{'selected':'','conversations':{}})
        self.assertEqual(fields['selected_conversation']['enum'],[c.label(r) for r in self.rows])
        self.assertNotEqual(c.key(self.rows[0]),c.key({**self.rows[0],'hostId':'other'}))

    def test_settings_inheritance(self):
        defaults={'default_mode':'notify','volume':90,'bt_style':True,'auto_send':True,'summary_length':'short'}
        self.assertEqual(c.preferences(c.DEFAULT,defaults)['volume'],90)
        effective=c.preferences({**c.DEFAULT,'volume':22,'bt_style':'off','mode':'reply'},defaults)
        self.assertEqual(effective['volume'],22)
        self.assertFalse(effective['bt_style'])
        self.assertEqual(effective['mode'],'reply')

    def test_each_setting_is_one_select_with_general_and_concrete_values(self):
        fields,values,_=c.describe(self.rows,{'selected':'','conversations':{}})
        prefix='conversation__'+c.key(self.rows[0])+'__'
        self.assertFalse(any(k.endswith('_inherit') for k in fields))
        self.assertEqual(len([k for k in fields if k.startswith(prefix)]),7)
        for field in ['mode','bt_style','summary_length','auto_send']:
            self.assertEqual(fields[prefix+field]['type'],'string')
            self.assertEqual(fields[prefix+field]['enum'][0],'通用')
            self.assertEqual(values[prefix+field],'通用')
        self.assertEqual(fields[prefix+'mode']['enum'],['通用','双向语音','只播报回复','只通知结果'])
        self.assertEqual(fields[prefix+'bt_style']['enum'],['通用','开启','关闭'])
        self.assertEqual(fields[prefix+'summary_length']['enum'],['通用','简短','正常'])
        self.assertEqual(fields[prefix+'volume']['type'],'integer')
        self.assertNotIn('enum',fields[prefix+'volume'])
        self.assertEqual(fields[prefix+'volume_source']['enum'],['通用','自定义'])

    def test_select_roundtrip_preserves_false_and_inheritance(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'settings.json';prefix='conversation__'+c.key(self.rows[0])+'__'
            defaults={'default_mode':'reply','volume':63,'bt_style':True,'auto_send':True,'summary_length':'short'}
            for field,display,stored in [('bt_style','关闭','off'),('auto_send','开启','on'),('mode','只通知结果','notify'),('volume',23,23)]:
                c.update({prefix+field:display},self.rows,path)
                item=c.read(path)['conversations'][c.key(self.rows[0])]
                self.assertEqual(item[field],stored)
                self.assertEqual(c.describe(self.rows,c.read(path))[1][prefix+field],display)
                c.update({prefix+field:'通用'},self.rows,path)
                if field=='volume':self.assertEqual(c.describe(self.rows,c.read(path))[1][prefix+'volume_source'],'通用')
                else:self.assertEqual(c.describe(self.rows,c.read(path))[1][prefix+field],'通用')
            self.assertEqual(c.preferences(c.read(path)['conversations'][c.key(self.rows[0])],defaults)['volume'],63)

if __name__=='__main__':unittest.main()
