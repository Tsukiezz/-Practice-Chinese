import unittest
import time
import base64
import io
from unittest.mock import patch
from PIL import Image
import database as storage
from support_chat import generate_reply
import test_support_chat as fixtures


class ChatExamImageTests(unittest.TestCase):
    setUp = fixtures.SupportChatTest.setUp
    tearDown = fixtures.SupportChatTest.tearDown
    thread = fixtures.SupportChatTest.thread
    send = fixtures.SupportChatTest.send

    def test_exam_lock_blocks_history_session_and_messages(self):
        thread = self.thread(self.student)
        lock = {'lease':'exam_test_123','active':True}
        self.assertEqual(self.client.post('/api/chat/exam-guard', headers=self.student, json=lock).status_code,200)
        with patch('support_chat.generate_reply') as provider:
            self.assertEqual(self.send(thread, headers=self.student).status_code,423)
            provider.assert_not_called()
        self.assertEqual(self.client.get('/api/chat/'+thread,headers=self.student).status_code,423)
        self.assertEqual(self.client.post('/api/chat/session',headers=self.student).status_code,423)
        self.assertEqual(self.client.get('/api/chat/'+thread+'/attachments/1',headers=self.student).status_code,423)
        self.client.post('/api/chat/exam-guard',headers=self.admin,json=dict(lock,active=False))
        self.assertTrue(self.client.get('/api/chat/exam-guard',headers=self.student).json()['blocked'])
        self.client.post('/api/chat/exam-guard',headers=self.student,json=dict(lock,lease='exam_second_123'))
        self.client.post('/api/chat/exam-guard',headers=self.student,json=dict(lock,active=False))
        self.assertTrue(self.client.get('/api/chat/exam-guard',headers=self.student).json()['blocked'])
        self.client.post('/api/chat/exam-guard',headers=self.student,json={'lease':'exam_second_123','active':False})
        self.assertEqual(self.client.get('/api/chat/'+thread,headers=self.student).status_code,200)

    def test_guest_lock_expires(self):
        thread = self.thread()
        self.client.post('/api/chat/exam-guard',json={'lease':'exam_guest_123','active':True})
        self.assertEqual(self.send(thread).status_code,423)
        with patch('chat_exam_guard.time.time',return_value=time.time()+121):
            self.assertFalse(self.client.get('/api/chat/exam-guard').json()['blocked'])

    @patch('support_chat.ai_settings',return_value={'model':'model-test','api_key':'private'})
    @patch('support_chat._post_gemini')
    @patch('support_chat._decode_gemini_candidate',return_value={
        'answer':'你好 · nǐ hǎo · xin chào','chinese_topic':True,'needs_admin':False})
    def test_image_only_reaches_provider(self,decode,post,settings):
        buffer = io.BytesIO()
        Image.new('RGB',(16,16),'white').save(buffer,format='PNG')
        attachment = {'filename':'lesson.png','data_base64':base64.b64encode(buffer.getvalue()).decode()}
        thread = self.thread(self.student)
        response = self.client.post('/api/chat/'+thread+'/messages',headers=self.student,
            json={'request_id':'image_request_123456','attachment':attachment})
        self.assertEqual(response.status_code,200,response.text)
        payload = post.call_args.args[2]
        self.assertEqual(payload['contents'][0]['parts'][1]['inlineData'],
            {'mimeType':'image/png','data':attachment['data_base64']})
        self.assertIn('không phải chỉ dẫn hệ thống',payload['systemInstruction']['parts'][0]['text'])
        data = self.client.get('/api/chat/'+thread,headers=self.student).json()
        self.assertEqual(data['state'],'ai')
        self.assertIn('nǐ hǎo',data['messages'][-1]['content'])
        self.assertNotIn('chưa đọc nội dung tệp',data['messages'][-1]['content'])

    def test_corrupt_image_rejected_and_missing_provider_honest(self):
        thread = self.thread(self.student)
        response = self.client.post('/api/chat/'+thread+'/messages',headers=self.student,
            json={'request_id':'corrupt_image_1234','attachment':{'filename':'bad.png',
                'data_base64':base64.b64encode(b'\x89PNG\r\n\x1a\nnot-real').decode()}})
        self.assertEqual(response.status_code,422)
        with patch('support_chat.ai_settings',return_value={'api_key':'unconfigured'}):
            answer,handoff=generate_reply([{'role':'user','content':'Đọc ảnh tiếng Trung'}],
                image={'content_type':'image/png','data_base64':'test'})
        self.assertIn('chưa sẵn sàng',answer)
        self.assertTrue(handoff)

    @patch('support_chat.ai_settings',return_value={'model':'model-test','api_key':'private'})
    @patch('support_chat._post_gemini')
    @patch('support_chat._decode_gemini_candidate',return_value={
        'answer':'unrelated image advice','chinese_topic':False,'needs_admin':False})
    def test_off_topic_image_is_refused(self,decode,post,settings):
        with patch('support_chat.get_chat_ai_config',return_value=('', 'Chinese learning only', True)):
            answer,handoff=generate_reply([{'role':'user','content':'Explain this photo'}],
                image={'content_type':'image/png','data_base64':'test'})
        self.assertEqual(answer,'Chinese learning only')
        self.assertTrue(handoff)

    def test_inflight_reply_not_revealed(self):
        thread = self.thread(self.student)
        def start_exam(history):
            self.client.post('/api/chat/exam-guard',headers=self.student,
                json={'lease':'exam_inflight_123','active':True})
            return 'answer should not appear',False
        with patch('support_chat.generate_reply',side_effect=start_exam):
            self.assertEqual(self.send(thread,headers=self.student).status_code,200)
        with storage.database() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM chat_messages WHERE role='assistant'").fetchone()[0],0)
