"""Admin audit pagination, complete details and chat history windows."""
import hashlib
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
import database as storage
from main import app
from support_chat import init_chat


class AdminSystemTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old = storage.DB_PATH
        storage.DB_PATH = Path(self.temp.name) / 'admin-system.db'
        storage.init_db()
        init_chat()
        self.client = TestClient(app)
        with storage.database() as conn:
            for role in ('admin', 'student'):
                cur = conn.execute('INSERT INTO users(name,email,password_hash,salt,role,created_at) VALUES(?,?,?,?,?,?)',
                                   (role, role+'@system.test', 'unused', 'unused', role, int(time.time())))
                conn.execute('INSERT INTO sessions VALUES(?,?,?)',
                             (hashlib.sha256(('system-'+role).encode()).hexdigest(),cur.lastrowid,int(time.time())+3600))
                if role == 'admin':
                    self.admin_id = cur.lastrowid
        self.headers = {'Authorization':'Bearer system-admin'}

    def tearDown(self):
        self.client.close()
        storage.DB_PATH = self.old
        self.temp.cleanup()

    def test_logs_filters_pagination_details_and_legacy_contract(self):
        with storage.database() as conn:
            for i in range(125):
                storage.audit(conn,self.admin_id,'update' if i % 2 else 'create',
                              'vocabulary',i,{'meaning':'before-'+str(i)}, {'meaning':'after-'+str(i)})
            conn.execute('UPDATE audit_logs SET created_at=1000 WHERE id<=100')
            conn.execute('UPDATE audit_logs SET created_at=2000 WHERE id>100')
        path = '/api/admin/audit-logs'
        self.assertEqual(self.client.get(path).status_code,401)
        self.assertEqual(self.client.get(path,headers={'Authorization':'Bearer system-student'}).status_code,403)
        first = self.client.get(path+'?paginated=true&limit=50',headers=self.headers).json()
        self.assertEqual((first['total'],len(first['items'])),(125,50))
        ids = []
        for offset in (0,50,100):
            data = self.client.get(path+'?paginated=true&limit=50&offset='+str(offset),headers=self.headers).json()
            ids.extend(row['id'] for row in data['items'])
        self.assertEqual(len(set(ids)),125)
        self.assertEqual(ids,sorted(ids,reverse=True))
        self.assertIn('before-',first['items'][0]['before_json'])
        self.assertEqual(first['actors'][0]['id'],self.admin_id)
        recent = self.client.get(path+'?paginated=true&from_ts=2000&to_ts=2001',headers=self.headers).json()
        self.assertEqual(recent['total'],25)
        filtered = self.client.get(path,params={'paginated':True,'action':'update','entity':'vocabulary','actor_id':self.admin_id,'search':'after-123'},headers=self.headers).json()
        self.assertEqual(filtered['total'],1)
        self.assertEqual(self.client.get(path+'?from_ts=2001&to_ts=1000',headers=self.headers).status_code,422)
        self.assertIsInstance(self.client.get(path,headers=self.headers).json(),list)
        self.assertEqual(self.client.get(path+'?paginated=true&search=nothing-found',headers=self.headers).json()['total'],0)

    def test_latest_chat_history_can_page_back_without_loss(self):
        thread = self.client.post('/api/chat/session').json()['id']
        with storage.database() as conn:
            for i in range(130):
                conn.execute("INSERT INTO chat_messages(thread_id,role,content,created_at) VALUES(?,'user',?,?)",
                             (thread,str(i),int(time.time())))
        path = '/api/admin/chats/'+thread
        first = self.client.get(path+'?recent=true',headers=self.headers).json()
        self.assertEqual(len(first['messages']),50)
        self.assertEqual(first['messages'][-1]['content'],'129')
        self.assertTrue(first['has_older'])
        second = self.client.get(path+'?before='+str(first['messages'][0]['id']),headers=self.headers).json()
        third = self.client.get(path+'?before='+str(second['messages'][0]['id']),headers=self.headers).json()
        self.assertFalse(third['has_older'])
        messages = third['messages']+second['messages']+first['messages']
        self.assertEqual([row['content'] for row in messages],[str(i) for i in range(130)])
        self.assertEqual(self.client.get(path+'?after='+str(first['messages'][-1]['id']),headers=self.headers).json()['messages'],[])

    def test_chat_actions_are_audited_once_on_retries(self):
        thread = self.client.post('/api/chat/session').json()['id']
        path = '/api/admin/chats/'+thread
        for _ in range(2):
            self.client.patch(path,headers=self.headers,json={'state':'admin'})
            response = self.client.post(path+'/messages',headers=self.headers,
                json={'content':'Nội dung hỗ trợ đầy đủ','request_id':'system_request_12345'})
            self.assertEqual(response.status_code,200)
        self.client.patch(path,headers=self.headers,json={'state':'ai'})
        logs = self.client.get('/api/admin/audit-logs?entity=chat',headers=self.headers).json()
        self.assertEqual([row['action'] for row in logs],['resume_ai','reply','takeover'])
        self.assertIn('Nội dung hỗ trợ đầy đủ',logs[1]['after_json'])

    @patch.dict(os.environ,{'GEMINI_API_KEY':'private-test-key'})
    @patch('ai_provider.gemini_grade',return_value={'score':100,'feedback':'OK'})
    def test_ai_usage_summary_and_connection_audit(self, provider):
        with storage.database() as conn:
            conn.execute("UPDATE ai_config SET enabled=1,model='test-model' WHERE id=1")
            conn.execute("INSERT INTO ai_usage(user_id,module,status,created_at) VALUES(?,'reading','error',?)",
                         (self.admin_id,int(time.time())-90000))
        result = self.client.post('/api/admin/ai-config/test',headers=self.headers)
        self.assertEqual(result.status_code,200)
        config = self.client.get('/api/admin/ai-config',headers=self.headers)
        self.assertEqual(config.json()['usage_24h'],{'success':1})
        self.assertNotIn('private-test-key',config.text)
        self.assertEqual(config.json()['recent_usage'][0]['module'],'connection_test')
        logs = self.client.get('/api/admin/audit-logs?action=connection_test',headers=self.headers).json()
        self.assertEqual(len(logs),1)
        self.assertNotIn('private-test-key',str(logs))
        self.assertIn('success',logs[0]['after_json'])


if __name__ == '__main__':
    unittest.main()
