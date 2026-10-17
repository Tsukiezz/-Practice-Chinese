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
    def test_current_product_guidance_for_google_and_compact_writing_tools(self):
        from support_chat import local_hanzigo_tutor, is_on_topic_chinese_or_hanzigo
        for question, expected in [
            ('Đổi tên Google ở đâu?', 'Cá nhân'),
            ('Chọn cọ viết tay thế nào?', 'Chọn cọ viết tay'),
            ('Màu mực ở đâu?', 'ô Màu mực'),
            ('Nút quay lại ở đâu?', 'thanh điều hướng'),
        ]:
            self.assertTrue(is_on_topic_chinese_or_hanzigo(question))
            answer, handoff = local_hanzigo_tutor([{'role': 'user', 'content': question}])
            self.assertIn(expected, answer)
            self.assertFalse(handoff)

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
        from support_chat import get_chat_ai_config
        self.assertEqual(generate_reply([{'role':'user','content':'hello'}]),(get_chat_ai_config()[1],True))
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

    def test_off_topic_questions_strictly_declined_and_handed_off_to_admin(self):
        from support_chat import OFF_TOPIC_DECLINE_MESSAGE
        off_topics = [
            'cầu thủ nào hay nhất thế giới mọi thời đại',
            'messi hơn ronaldo đúng không',
            'có thể code cho tôi một chương trình C hay không',
            'hiếu thứ hai đẹp không',
            'con cá chiên hay nướng ngon hơn',
            'thời tiết ngày mai thế nào',
        ]
        for query in off_topics:
            reply, handoff = generate_reply([{'role': 'user', 'content': query}])
            self.assertEqual(reply, OFF_TOPIC_DECLINE_MESSAGE)
            self.assertTrue(handoff)

        # Test end-to-end API send and admin inbox queue
        thread = self.thread()
        res = self.send(thread, 'cầu thủ nào hay nhất thế giới mọi thời đại', 'req_offtopic_1111')
        self.assertEqual(res.status_code, 200)
        data = self.client.get('/api/chat/' + thread).json()
        self.assertEqual(data['state'], 'waiting')
        last_msg = data['messages'][-1]['content']
        self.assertIn('không có nghĩa vụ giải đáp', last_msg)
        self.assertIn('chuyển tiếp đến Quản trị viên (Admin)', last_msg)
        self.assertTrue(last_msg.endswith(HANDOFF))

    @patch('support_chat.ai_settings', return_value={'model': 'model-test', 'api_key': 'unconfigured'})
    def test_local_hanzigo_tutor_answers_chinese_and_app_queries(self, settings):
        # Greetings
        ans, handoff = generate_reply([{'role': 'user', 'content': 'Xin chào'}])
        self.assertIn('Trợ lý AI HanziGo', ans)
        self.assertFalse(handoff)

        # Exam guidance
        ans, handoff = generate_reply([{'role': 'user', 'content': 'Cách tạo đề thi AI 40 câu'}])
        self.assertIn('1 đến 50 câu', ans)
        self.assertFalse(handoff)

        # Dark mode guidance
        ans, handoff = generate_reply([{'role': 'user', 'content': 'Làm sao để bật chế độ tối dark mode'}])
        self.assertIn('Chế độ Tối', ans)
        self.assertFalse(handoff)

    @patch('support_chat.ai_settings', return_value={'model': 'model-test', 'api_key': 'unconfigured'})
    def test_local_hanzigo_tutor_declines_off_topic_queries(self, settings):
        from support_chat import OFF_TOPIC_DECLINE_MESSAGE, local_hanzigo_tutor
        for q in ['hiếu thứ hai đẹp không', 'con cá chiên hay nướng ngon hơn', 'thời tiết hôm nay thế nào']:
            ans, handoff = local_hanzigo_tutor([{'role': 'user', 'content': q}])
            self.assertEqual(ans, OFF_TOPIC_DECLINE_MESSAGE)
            self.assertTrue(handoff)

    def test_admin_can_configure_and_train_support_ai(self):
        # 1. Admin gets current AI config with chat prompt & settings
        config = self.client.get('/api/admin/ai-config', headers=self.admin).json()
        self.assertIn('chat_prompt', config)
        self.assertIn('chat_decline_message', config)
        self.assertIn('chat_strict_mode', config)
        self.assertIn('chat_stats', config)
        self.assertTrue(config['chat_strict_mode'])

        # 2. Admin customizes the training prompt and decline message
        custom_prompt = 'Huấn luyện riêng cho trợ lý: Luôn trả lời ngắn gọn về tiếng Trung.'
        custom_decline = 'Xin lỗi, câu hỏi này nằm ngoài phạm vi học tập HanziGo của chúng tôi.'
        update_payload = {
            'model': config['model'],
            'system_prompt': config['system_prompt'],
            'temperature': config['temperature'],
            'max_tokens': config['max_tokens'],
            'enabled': bool(config['enabled']),
            'version': config['version'],
            'chat_prompt': custom_prompt,
            'chat_decline_message': custom_decline,
            'chat_strict_mode': True
        }
        res = self.client.put('/api/admin/ai-config', headers=self.admin, json=update_payload)
        self.assertEqual(res.status_code, 200)
        updated = res.json()
        self.assertEqual(updated['chat_prompt'], custom_prompt)
        self.assertEqual(updated['chat_decline_message'], custom_decline)
        self.assertTrue(updated['chat_strict_mode'])

        # 3. Verify support chat now returns the custom decline message for off-topic query
        ans, handoff = generate_reply([{'role': 'user', 'content': 'hiếu thứ hai đẹp không'}])
        self.assertEqual(ans, custom_decline)
        self.assertTrue(handoff)

    @patch('support_chat.generate_reply', return_value=('Reply in current session', False))
    def test_idle_expiry_hides_history_from_guest_and_student_but_retains_admin(self, provider):
        for headers in ({}, self.student):
            now = int(time.time())
            with patch('support_chat.time.time', return_value=now):
                thread = self.thread(headers)
                self.assertEqual(self.send(thread, headers=headers).status_code, 200)
            with patch('support_chat.time.time', return_value=now + 299):
                live = self.client.get('/api/chat/' + thread, headers=headers).json()
                self.assertTrue(live['active'])
                self.assertEqual(self.client.post('/api/chat/session', headers=headers).json()['expires_at'], now + 300)
            with patch('support_chat.time.time', return_value=now + 300):
                ended = self.client.get('/api/chat/' + thread, headers=headers).json()
                self.assertFalse(ended['active'])
                self.assertEqual(ended['messages'], [])
                self.assertEqual(self.send(thread, key='request_after_expiry', headers=headers).status_code, 410)
                archive = self.client.get('/api/admin/chats/' + thread, headers=self.admin).json()
                self.assertEqual(len(archive['messages']), 2)
                self.assertEqual(archive['state'], 'closed')
                self.assertEqual(self.client.get('/api/admin/chats?state=closed', headers=self.admin).status_code, 200)
                restarted = self.client.post('/api/chat/session', headers=headers).json()
                self.assertTrue(restarted['active'])
                self.assertEqual(restarted['messages'], [])
                stale = self.client.post('/api/chat/' + thread + '/messages', headers=headers,
                    json={'content': 'stale tab', 'request_id': 'request_old_session', 'session_key': live['session_key']})
                self.assertEqual(stale.status_code, 410)
                self.send(thread, text='New question', key='request_new_session', headers=headers)
                self.assertEqual(provider.call_args.args[0], [{'role': 'user', 'content': 'New question'}])
                fresh = self.client.get('/api/chat/' + thread + '?after=0', headers=headers).json()
                self.assertEqual(len(fresh['messages']), 2)
                self.assertEqual(len(self.client.get('/api/admin/chats/' + thread, headers=self.admin).json()['messages']), 4)

    def test_legacy_history_is_admin_only_and_admin_cannot_reopen_expired_session(self):
        thread = self.thread(self.student)
        with storage.database() as conn:
            conn.execute("INSERT INTO chat_messages(thread_id,role,content,created_at) VALUES(?,'user','old message',?)", (thread, int(time.time())))
            conn.execute('DELETE FROM chat_sessions WHERE thread_id=?', (thread,))
        self.assertEqual(self.client.get('/api/chat/' + thread, headers=self.student).json()['messages'], [])
        self.assertEqual(len(self.client.get('/api/admin/chats/' + thread, headers=self.admin).json()['messages']), 1)
        self.assertEqual(self.client.post('/api/admin/chats/' + thread + '/messages', headers=self.admin,
            json={'content':'late reply','request_id':'admin_late_reply_123'}).status_code, 410)
        self.assertEqual(self.client.patch('/api/admin/chats/' + thread, headers=self.admin, json={'state':'ai'}).status_code, 410)
        self.assertEqual(self.client.post('/api/chat/session', headers=self.student).json()['messages'], [])

    @patch('support_chat.generate_reply', return_value=('Reply', False))
    def test_admin_reply_restarts_idle_clock(self, provider):
        now = int(time.time())
        with patch('support_chat.time.time', return_value=now):
            thread = self.thread()
            self.send(thread)
        with patch('support_chat.time.time', return_value=now + 240):
            self.client.post('/api/admin/chats/' + thread + '/messages', headers=self.admin,
                json={'content':'Human support','request_id':'admin_response_1234'})
        with patch('support_chat.time.time', return_value=now + 301):
            self.assertTrue(self.client.get('/api/chat/' + thread).json()['active'])
        with patch('support_chat.time.time', return_value=now + 540):
            self.assertFalse(self.client.get('/api/chat/' + thread).json()['active'])

    def test_private_files_follow_session_boundary_and_remain_in_admin_archive(self):
        import base64
        file = {'filename': 'lesson.txt', 'data_base64': base64.b64encode(b'Chinese learning notes').decode()}
        thread = self.thread(self.student)
        request = {'attachment': file, 'request_id': 'request_attachment_123'}
        for _ in range(2):
            self.assertEqual(self.client.post('/api/chat/' + thread + '/messages', headers=self.student, json=request).status_code, 200)
        data = self.client.get('/api/chat/' + thread, headers=self.student).json()
        self.assertEqual(data['state'], 'waiting')
        self.assertEqual(len(data['messages']), 2)
        attached = data['messages'][0]['attachment']
        self.assertEqual(attached['filename'], 'lesson.txt')
        self.assertNotIn('data_base64', attached)
        url = '/api/chat/' + thread + '/attachments/' + str(attached['id'])
        self.assertEqual(self.client.get(url, headers=self.student).json()['data_base64'], file['data_base64'])
        self.assertEqual(self.client.get(url).status_code, 404)
        admin_url = '/api/admin/chats/' + thread + '/attachments/' + str(attached['id'])
        self.assertEqual(self.client.get(admin_url, headers=self.student).status_code, 403)
        with storage.database() as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM chat_attachments').fetchone()[0], 1)
            conn.execute('UPDATE chat_sessions SET expires_at=0 WHERE thread_id=?', (thread,))
        self.assertEqual(self.client.get(url, headers=self.student).status_code, 410)
        self.client.post('/api/chat/session', headers=self.student)
        self.assertEqual(self.client.get(url, headers=self.student).status_code, 404)
        archived = self.client.get(admin_url, headers=self.admin)
        self.assertEqual(archived.status_code, 200)
        self.assertIn('no-store', archived.headers['cache-control'])
        self.assertEqual(archived.json()['data_base64'], file['data_base64'])

    def test_admin_can_send_file_to_guest_and_invalid_uploads_leave_no_messages(self):
        import base64
        thread = self.thread()
        file = {'filename': 'guide.pdf', 'data_base64': base64.b64encode(b'%PDF-1.4\nexample').decode()}
        response = self.client.post('/api/admin/chats/' + thread + '/messages', headers=self.admin,
            json={'attachment': file, 'request_id':'admin_attachment_123'})
        self.assertEqual(response.status_code, 200, response.text)
        messages = self.client.get('/api/chat/' + thread).json()['messages']
        self.assertEqual(messages[0]['role'], 'admin')
        self.assertEqual(messages[0]['attachment']['content_type'], 'application/pdf')
        for name, content in [('evil.html', b'<script>hi</script>'), ('fake.png', b'not an image'), ('large.txt', b'x' * (2*1024*1024+1))]:
            response = self.client.post('/api/chat/' + thread + '/messages', json={
                'attachment':{'filename':name, 'data_base64':base64.b64encode(content).decode()},
                'request_id':'request_invalid_file'})
            self.assertGreaterEqual(response.status_code, 400)
        self.assertEqual(len(self.client.get('/api/chat/' + thread).json()['messages']), 1)

    def test_docx_and_text_file_validation(self):
        import base64, io, zipfile
        from support_attachments import AttachmentInput, validate_attachment
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as archive:
            archive.writestr('[Content_Types].xml', '<Types/>')
            archive.writestr('word/document.xml', '<document/>')
        data = validate_attachment(AttachmentInput(filename='../notes.docx', data_base64=base64.b64encode(buffer.getvalue()).decode()))
        self.assertEqual(data['filename'], 'notes.docx')
        self.assertIn('wordprocessingml', data['content_type'])


if __name__ == '__main__':
    unittest.main()


