"""Chat ownership, AI handoff, durable history and human takeover."""
import hashlib
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
import database as storage
from main import app
from support_chat import HANDOFF, init_chat, generate_reply


class SupportChatTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old = storage.DB_PATH
        storage.DB_PATH = Path(self.temp.name) / 'chat.db'
        storage.init_db()
        init_chat()
        self.client = TestClient(app)
        self.student = {'Authorization': 'Bearer student-chat-token'}
        self.admin = {'Authorization': 'Bearer admin-chat-token'}
        with storage.database() as conn:
            for name, role in [('student', 'student'), ('admin', 'admin')]:
                cur = conn.execute('INSERT INTO users(name,email,password_hash,salt,role,created_at) VALUES(?,?,?,?,?,?)',
                                   (name, name+'@chat.test', 'unused', 'unused', role, int(time.time())))
                conn.execute('INSERT INTO sessions VALUES(?,?,?)',
                             (hashlib.sha256((name+'-chat-token').encode()).hexdigest(), cur.lastrowid, int(time.time())+3600))

    def tearDown(self):
        self.client.close()
        storage.DB_PATH = self.old
        self.temp.cleanup()

    def thread(self, headers=None):
        response = self.client.post('/api/chat/session', headers=headers or {})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()['id']

    def send(self, thread, text='Giải thích chữ 你好', key='request_1234567890', headers=None):
        return self.client.post('/api/chat/'+thread+'/messages',
            json={'content':text,'request_id':key}, headers=headers or {})

    def test_guest_cookie_is_private_and_cannot_read_another_guest(self):
        thread = self.thread()
        self.assertEqual(self.thread(), thread)
        other = TestClient(app)
        self.assertEqual(other.get('/api/chat/'+thread).status_code,404)
        self.assertEqual(other.post('/api/chat/'+thread+'/messages',json={'content':'test','request_id':'request_1234567890'}).status_code,404)
        self.assertEqual(self.client.get('/api/admin/chats').status_code,401)
        self.assertEqual(self.client.get('/api/admin/chats',headers=self.student).status_code,403)
        other.close()

    def test_student_identity_survives_cookie_loss_and_rejects_invalid_auth(self):
        guest = self.thread()
        student = self.thread(self.student)
        self.assertNotEqual(guest,student)
        self.assertEqual(self.client.get('/api/chat/'+guest,headers=self.student).status_code,404)
        self.client.cookies.clear()
        self.assertEqual(self.thread(self.student),student)
        self.assertEqual(self.client.get('/api/chat/'+student).status_code,404)
        self.assertEqual(self.client.post('/api/chat/session',headers={'Authorization':'Bearer invalid'}).status_code,401)

    @patch('support_chat.generate_reply', return_value=('你好 · nǐ hǎo · Xin chào. Hãy tập đọc từng thanh.',False))
    def test_chinese_reply_persists_and_retry_does_not_duplicate(self, provider):
        thread = self.thread()
        self.assertEqual(self.send(thread).status_code,200)
        self.assertEqual(self.send(thread).status_code,200)
        data = self.client.get('/api/chat/'+thread).json()
        self.assertEqual(data['state'],'ai')
        self.assertEqual([m['role'] for m in data['messages']],['user','assistant'])
        self.assertNotIn(HANDOFF,data['messages'][1]['content'])
        self.assertEqual(provider.call_count,1)
        self.assertEqual(self.client.get('/api/admin/chats/'+thread,headers=self.admin).json()['messages'],data['messages'])

    @patch('support_chat.generate_reply', return_value=('Bạn có thể thử tải lại trang và kiểm tra kết nối.',True))
    def test_off_topic_attempt_precedes_exact_handoff_and_admin_reply(self, provider):
        thread = self.thread()
        self.send(thread,'Tôi gặp lỗi thanh toán')
        data = self.client.get('/api/chat/'+thread).json()
        self.assertEqual(data['state'],'waiting')
        self.assertTrue(data['messages'][-1]['content'].endswith(HANDOFF))
        self.assertTrue(data['messages'][-1]['content'].startswith('Bạn có thể'))
        waiting = self.client.get('/api/admin/chats?state=waiting',headers=self.admin).json()
        self.assertEqual(waiting['total'],1)
        response = self.client.post('/api/admin/chats/'+thread+'/messages',headers=self.admin,
            json={'content':'Tôi sẽ kiểm tra cho bạn.','request_id':'admin_request_12345'})
        self.assertEqual(response.status_code,200)
        self.send(thread,'Cảm ơn','request_2222222222')
        self.assertEqual(provider.call_count,1)
        data = self.client.get('/api/chat/'+thread).json()
        self.assertEqual(data['state'],'admin')
        self.assertEqual(data['messages'][-2]['role'],'admin')
        self.client.patch('/api/admin/chats/'+thread,headers=self.admin,json={'state':'ai'})
        self.send(thread,'Học HSK nhé','request_3333333333')
        self.assertEqual(provider.call_count,2)

    @patch('support_chat.generate_reply',side_effect=RuntimeError('provider-secret-must-not-leak'))
    def test_ai_failure_keeps_user_message_and_hands_off(self, provider):
        thread = self.thread()
        self.assertEqual(self.send(thread).status_code,200)
        data = self.client.get('/api/chat/'+thread).json()
        self.assertEqual(data['state'],'waiting')
        self.assertNotIn('provider-secret',str(data))
        self.assertIn(HANDOFF,data['messages'][-1]['content'])

    def test_admin_takes_over_during_generation(self):
        thread = self.thread()
        def takeover(history):
            self.client.patch('/api/admin/chats/'+thread,headers=self.admin,json={'state':'admin'})
            return 'Late AI answer',False
        with patch('support_chat.generate_reply',side_effect=takeover):
            self.send(thread)
        data = self.client.get('/api/chat/'+thread).json()
        self.assertEqual(data['state'],'admin')
        self.assertEqual(len(data['messages']),1)

    def test_limits_whitespace_and_full_history_pagination(self):
        thread = self.thread()
        self.assertEqual(self.send(thread,'   ').status_code,422)
        self.assertEqual(self.send(thread,'x'*3001).status_code,422)
        with storage.database() as conn:
            conn.execute('UPDATE chat_threads SET busy_until=? WHERE id=?',(int(time.time())+55,thread))
        self.assertEqual(self.send(thread).status_code,409)
        with storage.database() as conn:
            conn.execute('UPDATE chat_threads SET busy_until=0 WHERE id=?',(thread,))
            for i in range(105):
                conn.execute("INSERT INTO chat_messages(thread_id,role,content,created_at) VALUES(?,'user',?,?)",(thread,str(i),int(time.time())))
        first = self.client.get('/api/chat/'+thread).json()['messages']
        rest = self.client.get('/api/chat/'+thread+'?after='+str(first[-1]['id'])).json()['messages']
        self.assertEqual(len(first)+len(rest),105)
        self.assertEqual(self.send(thread).status_code,429)

    @patch('support_chat.ai_settings', return_value={'model':'model-test','api_key':'private'})
    @patch('support_chat._post_gemini')
    @patch('support_chat._decode_gemini_candidate')
    def test_provider_routing_requires_valid_booleans(self, decode, post, settings):
        decode.return_value = {'answer':'helpful answer','chinese_topic':False,'needs_admin':False}
        self.assertEqual(generate_reply([{'role':'user','content':'hello'}]),('helpful answer',True))
        decode.return_value['chinese_topic'] = True
        self.assertEqual(generate_reply([]),('helpful answer',False))
        self.assertEqual(generate_reply([{'role':'user','content':'Tôi muốn liên hệ quản trị viên'}]),('helpful answer',True))
        self.assertEqual(generate_reply([{'role':'user','content':'Tôi không muốn liên hệ admin, hãy giải thích ngữ pháp.'}]),('helpful answer',False))
        # Old contact requests must not force all later turns into handoff.
        self.assertEqual(generate_reply([{'role':'user','content':'Tôi muốn gặp admin'},
            {'role':'user','content':'Giải thích ngữ pháp 把'}]),('helpful answer',False))
        decode.return_value['needs_admin'] = 'false'
        with self.assertRaises(ValueError):
            generate_reply([])


if __name__ == '__main__':
    unittest.main()
