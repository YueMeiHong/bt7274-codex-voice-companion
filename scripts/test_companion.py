# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

import unittest
from native_codex import final_answer


class NativeReplyTests(unittest.TestCase):
    def test_commentary_and_partial_reply_are_not_spoken(self):
        data={'turns':[{'id':'t','status':'inProgress','items':[
            {'type':'agentMessage','phase':'final_answer','id':'partial','text':'still streaming'}]}]}
        self.assertIsNone(final_answer(data))

    def test_final_answer_preserved_verbatim(self):
        text='测试失败：3/5。不要部署。'
        answer=final_answer({'turns':[{'id':'t','status':'completed','items':[
            {'type':'agentMessage','phase':'commentary','id':'a','text':'checking'},
            {'type':'agentMessage','phase':'final_answer','id':'b','text':text}]}]})
        self.assertEqual(answer['text'],text)

    def test_failure_and_interrupt_are_not_reported_as_success(self):
        for status,word in [('failed','失败'),('interrupted','中断')]:
            answer=final_answer({'turns':[{'id':'t','status':status,'items':[],'error':{'message':'test'}}]})
            self.assertIn(word,answer['text'])
            self.assertNotIn('成功',answer['text'])


if __name__=='__main__':unittest.main()
