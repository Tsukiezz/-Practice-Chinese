import os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
import database as storage
from main import app
from usecase_features import init_features

class AccountUseCaseTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory()
  self.old=storage.DB_PATH;storage.DB_PATH=Path(self.temp.name)/"test.db"
  self.client=TestClient(app);self.client.__enter__()
  r=self.client.post("/api/auth/register",json={"name":"Original","email":"owner@example.test","password":"Original-password-123"})
  self.assertEqual(r.status_code,201)
  self.token=r.json()["token"];self.headers={"Authorization":"Bearer "+self.token}
 def tearDown(self):
  self.client.__exit__(None,None,None);storage.DB_PATH=self.old;self.temp.cleanup()
 def test_profile_validation_and_owner_scope(self):
  self.assertEqual(self.client.get("/api/account").status_code,401)
  r=self.client.put("/api/account",headers=self.headers,json={"name":"New Name","phone":"+84 123456","birth_date":"2000-01-02","daily_goal":2,"weekly_goal":12})
  self.assertEqual(r.status_code,200,r.text)
  self.assertEqual(self.client.get("/api/me",headers=self.headers).json()["name"],"New Name")
  self.assertEqual(self.client.put("/api/account",headers=self.headers,json={"name":"x","avatar":"data:image/png;base64,YmFk"}).status_code,422)
  self.assertEqual(self.client.put("/api/account",headers=self.headers,json={"name":"x","birth_date":"2999-01-01"}).status_code,422)
 def test_password_old_check_and_revocation(self):
  self.assertEqual(self.client.post("/api/account/password",headers=self.headers,json={"old_password":"wrong","new_password":"New-password-123"}).status_code,400)
  self.assertEqual(self.client.post("/api/account/password",headers=self.headers,json={"old_password":"Original-password-123","new_password":"New-password-123"}).status_code,204)
  self.assertEqual(self.client.get("/api/me",headers=self.headers).status_code,401)
  self.assertEqual(self.client.post("/api/auth/login",json={"email":"owner@example.test","password":"New-password-123"}).status_code,200)
 def test_recovery_otp_expiration_attempts_and_single_use(self):
  sent=[]
  with patch("usecase_features.smtp_ready",return_value=True),patch("usecase_features.send_otp",side_effect=lambda email,code:sent.append(code)):
   self.assertEqual(self.client.post("/api/auth/recovery",json={"email":"owner@example.test"}).status_code,200)
  self.assertEqual(len(sent),1)
  body={"email":"owner@example.test","code":sent[0],"password":"Recovered-password-123"}
  self.assertEqual(self.client.post("/api/auth/recovery/confirm",json=body).status_code,204)
  self.assertEqual(self.client.post("/api/auth/recovery/confirm",json=body).status_code,400)
  self.assertEqual(self.client.get("/api/me",headers=self.headers).status_code,401)
 def test_guest_permissions_and_translation_limit(self):
  self.assertEqual(self.client.get("/api/me/saved-words").status_code,401)
  self.assertEqual(self.client.get("/api/admin/dashboard").status_code,401)
  self.assertEqual(self.client.post("/api/translation/text",json={"text":"x"*5001}).status_code,422)
  with patch("usecase_features.smtp_ready",return_value=False):
   self.assertEqual(self.client.post("/api/auth/recovery",json={"email":"owner@example.test"}).status_code,503)
 def test_goals_default_and_sentence_order_validation(self):
  result=self.client.get('/api/me/goals',headers=self.headers)
  self.assertEqual(result.status_code,200)
  self.assertEqual(result.json()['daily_done'],0)
  from models import Question
  from pydantic import ValidationError
  q=Question(id='order',section='writing',question_type='sentence_order',prompt='Arrange',options=['学习','我','中文'],answer='我 学习 中文')
  self.assertEqual(q.question_type,'sentence_order')
  with self.assertRaises(ValidationError):
   Question(id='order',section='writing',question_type='sentence_order',prompt='Arrange',options=['学习','我','中文'],answer='我 中文')
 def test_personalized_practice_is_private_and_saves_result(self):
  with storage.database() as c:
   u_row=c.execute('SELECT id FROM users WHERE email=?',('owner@example.test',)).fetchone()
   assert u_row is not None
   uid=u_row[0]
   c.execute("INSERT INTO results(user_id,kind,content,score,original_score,feedback,graded_by,created_at) VALUES(?,'writing','{}',50,50,'word order','ai',1)",(uid,))
  with patch('usecase_features.ai_settings',return_value={'model':'test','api_key':'not-a-key'}),patch('usecase_features._post_gemini',return_value=Mock()),patch('usecase_features._decode_gemini_candidate',return_value={'tasks':[{'prompt':'Write a sentence','hint':'Check word order'}]}):
   r=self.client.post('/api/me/personalized-practice',headers=self.headers)
  self.assertEqual(r.status_code,200,r.text)
  pid=r.json()['id']
  other=self.client.post('/api/auth/register',json={'name':'Other','email':'other@example.test','password':'Other-password-123'}).json()['token']
  self.assertEqual(self.client.post(f'/api/me/personalized-practice/{pid}/0',headers={'Authorization':'Bearer '+other},json={'text':'你好'}).status_code,404)
  with patch('services.grade_essay_with_ai',return_value={'score':90,'feedback':'Good'}):
   self.assertEqual(self.client.post(f'/api/me/personalized-practice/{pid}/0',headers=self.headers,json={'text':'你好'}).status_code,201)
  with storage.database() as c:
   cnt_row=c.execute('SELECT COUNT(*) FROM results WHERE user_id=?',(uid,)).fetchone()
   assert cnt_row is not None
   self.assertEqual(cnt_row[0],2)
if __name__=="__main__":unittest.main()
