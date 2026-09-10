"""Integration tests use isolated databases, never the developer's local data."""
import json
import base64
import os
import tempfile
import unittest
import httpx
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

import database as storage
from main import app
from seed import seed
from services import grade_with_ai, _post_gemini, _render_strokes_png


class AdminIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_db = storage.DB_PATH
        storage.DB_PATH = Path(self.temp.name) / "test.db"
        self.client = TestClient(app)
        self.client.__enter__()
        self.admin = self.register("admin@example.test", "Nguyên")
        self.student = self.register("student@example.test", "Học viên")
        with storage.database() as conn:
            conn.execute("UPDATE users SET role='admin' WHERE id=?", (self.admin["user"]["id"],))
        self.headers = {"Authorization": "Bearer " + self.admin["token"]}
        self.student_headers = {"Authorization": "Bearer " + self.student["token"]}

    def tearDown(self):
        self.client.__exit__(None, None, None)
        storage.DB_PATH = self.old_db
        self.temp.cleanup()

    def test_handwriting_renderer_creates_real_png_for_gemini(self):
        encoded = _render_strokes_png([
            [{"x": 100, "y": 500}, {"x": 900, "y": 500}],
        ], size=64)
        image = base64.b64decode(encoded)
        self.assertTrue(image.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertGreater(len(image), 100)

    def test_gemini_transient_failure_is_retried(self):
        request = httpx.Request("POST", "https://gemini.example.test")
        responses = [
            httpx.Response(503, request=request),
            httpx.Response(200, request=request, json={
                "candidates": [{"content": {"parts": [{"text": '{"ok": true}'}]}}]
            }),
        ]
        with patch("services.httpx.post", side_effect=responses) as post, \
             patch("services.time.sleep"):
            response = _post_gemini(
                str(request.url), {"x-goog-api-key": "secret"}, {}, 1.0)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(post.call_count, 2)

    def test_gemini_truncated_json_is_regenerated_with_more_tokens(self):
        request = httpx.Request("POST", "https://gemini.example.test")
        def candidate(text):
            return httpx.Response(200, request=request, json={
                "candidates": [{"content": {"parts": [{"text": text}]}}]
            })
        payload = {"generationConfig": {"maxOutputTokens": 500}}
        with patch("services.httpx.post", side_effect=[candidate('{"score":'),
                                                        candidate('{"score": 90}')]) as post:
            response = _post_gemini(str(request.url), {}, payload, 1.0)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(post.call_count, 2)
        self.assertEqual(payload["generationConfig"]["maxOutputTokens"], 2048)

    def register(self, email, name):
        response = self.client.post("/api/auth/register", json={"email": email, "name": name, "password": "Test-password-123"})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def post(self, path, body):
        return self.client.post("/api/admin" + path, json=body, headers=self.headers)

    def word(self):
        body = {"hanzi": "一", "pinyin": "yī", "meaning": "một", "hsk": 1,
                "strokes": [[{"x": 100, "y": 500}, {"x": 900, "y": 500}]]}
        response = self.post("/vocabulary", body)
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def exam(self, word=None, status="published", section="reading"):
        body = {"title": "HSK 1 mẫu", "hsk": 1, "status": status, "duration_minutes": 15,
                "questions": [{"id": "q1", "section": section, "prompt": "一 nghĩa là gì?",
                               "options": ["một", "hai"], "answer": "một", "explanation": "一 là một",
                               "audio_url": "https://example.test/audio.mp3" if section == "listening" else "",
                               "word_id": word["id"] if word else None}]}
        response = self.post("/exams", body)
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def submit(self, exam, answer="hai"):
        response = self.client.post(f"/api/exams/{exam['id']}/submit", headers=self.student_headers,
                                    json={"version": exam["version"], "answers": {"q1": answer}})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_admin_routes_deny_guest_and_student(self):
        for path in ("dashboard", "users", "vocabulary", "exams", "results", "ai-config", "audit-logs", "appeals"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get("/api/admin/" + path).status_code, 401)
                self.assertEqual(self.client.get("/api/admin/" + path, headers=self.student_headers).status_code, 403)
        self.assertEqual(self.client.post("/api/admin/vocabulary", headers=self.student_headers,
                                         json={"hanzi":"人","pinyin":"rén","meaning":"người","hsk":1}).status_code, 403)
        self.assertEqual(self.client.patch("/api/admin/users/1", headers=self.student_headers,
                                          json={"role":"admin","is_active":True}).status_code, 403)
        self.assertEqual(self.client.get("/admin").status_code, 200)

    def test_no_registration_role_escalation_or_invalid_email(self):
        body = {"name": "Evil", "email": "evil@example.test", "password": "Test-password-123", "role": "admin"}
        self.assertEqual(self.client.post("/api/auth/register", json=body).status_code, 422)
        body.pop("role")
        body["email"] = "invalid-email"
        self.assertEqual(self.client.post("/api/auth/register", json=body).status_code, 422)

    def test_user_conflict_and_idempotent_migration(self):
        storage.init_db()
        storage.init_db()
        path = f"/api/admin/users/{self.student['user']['id']}"
        body = {"role": "student", "is_active": True, "version": 1}
        self.assertEqual(self.client.patch(path, json=body, headers=self.headers).json()['version'], 2)
        self.assertEqual(self.client.patch(path, json=body, headers=self.headers).status_code, 409)
        self.assertEqual(self.client.get('/api/me', headers=self.student_headers).status_code, 200)

    def test_appeal_ownership_conflicts_resolution_and_history(self):
        with patch('main.grade_reading_exam', return_value={"score": 0, "feedback": "Test grade"}):
            result = self.submit(self.exam())
        path = f"/api/me/results/{result['id']}/appeals"
        reason = {'reason': 'Xin kiểm tra lại đáp án và điểm'}
        self.assertEqual(self.client.post(path, json=reason, headers=self.headers).status_code, 404)
        self.assertEqual(self.client.post(path, json={'reason':'x'}, headers=self.student_headers).status_code, 422)
        response = self.client.post(path, json=reason, headers=self.student_headers)
        self.assertEqual(response.status_code, 201)
        appeal = response.json()
        self.assertEqual(self.client.post(path, json=reason, headers=self.student_headers).status_code, 409)
        self.assertEqual(self.client.get('/api/me/appeals', headers=self.headers).json(), [])
        review_path = f"/api/admin/appeals/{appeal['id']}"
        body = {'version':1, 'result_version':1, 'score':85, 'response':'Đã đối chiếu và sửa điểm'}
        self.assertEqual(self.client.patch(review_path,json=body,headers=self.student_headers).status_code,403)
        self.assertEqual(self.client.patch(review_path,json={**body,'score':101},headers=self.headers).status_code,422)
        self.assertEqual(self.client.patch(review_path,json={**body,'result_version':2},headers=self.headers).status_code,409)
        self.assertEqual(self.client.get('/api/admin/appeals?status=pending',headers=self.headers).json()[0]['status'],'pending')
        self.assertEqual(self.client.patch(review_path,json=body,headers=self.headers).status_code,200)
        self.assertEqual(self.client.patch(review_path,json=body,headers=self.headers).status_code,409)
        updated = self.client.get('/api/me/results',headers=self.student_headers).json()[0]
        self.assertEqual(updated['score'],85)
        self.assertEqual(updated['original_score'],0)
        self.assertEqual(len(updated['overrides']),1)
        self.assertEqual(self.client.get('/api/admin/appeals?status=pending',headers=self.headers).json(),[])
        self.assertEqual(self.client.get('/api/me/appeals',headers=self.student_headers).json()[0]['response'],body['response'])

    def test_gemini_adapter_retry_timeout_and_invalid_output(self):
        import httpx
        from ai_provider import gemini_grade
        settings={'model':'test-model','api_key':'private-test-key','system_prompt':'Chấm bài','temperature':0.2,'max_tokens':1000}
        calls=[]
        def handler(request):
            calls.append(request)
            self.assertEqual(request.headers['x-goog-api-key'],'private-test-key')
            self.assertNotIn('private-test-key',str(request.url))
            if len(calls)==1:return httpx.Response(503)
            return httpx.Response(200,json={'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':'{"score":82,"feedback":"Tốt"}'}]}}]})
        output=gemini_grade(settings,'你好',transport=httpx.MockTransport(handler),sleep=lambda _:None)
        self.assertEqual(output['score'],82)
        self.assertEqual(len(calls),2)
        def timeout(request):
            raise httpx.ReadTimeout('private-test-key')
        for transport in (httpx.MockTransport(timeout),httpx.MockTransport(lambda _:httpx.Response(401,text='private-test-key')),
                          httpx.MockTransport(lambda _:httpx.Response(200,json={'candidates':[]}))):
            with self.assertRaises(ValueError) as error:
                gemini_grade(settings,'你好',transport=transport,sleep=lambda _:None)
            self.assertNotIn('private-test-key',str(error.exception))

    def test_ai_connection_test_is_private_and_does_not_create_results(self):
        self.assertEqual(self.client.post('/api/admin/ai-config/test',headers=self.student_headers).status_code,403)
        self.assertEqual(self.client.post('/api/admin/ai-config/test',headers=self.headers).status_code,503)
        with patch.dict(os.environ, {'AI_API_KEY':'private-test-key'}):
            self.client.put('/api/admin/ai-config',headers=self.headers,json={'model':'test-model','system_prompt':'Chấm bài','temperature':0.2,'max_tokens':1000,'enabled':True,'version':1})
            with patch('ai_provider.gemini_grade',return_value={'score':80,'feedback':'Tốt'}):
                self.assertEqual(self.client.post('/api/admin/ai-config/test',headers=self.headers).status_code,200)
            with patch('ai_provider.gemini_grade',side_effect=ValueError('private-test-key')):
                response=self.client.post('/api/admin/ai-config/test',headers=self.headers)
                self.assertEqual(response.status_code,502)
                self.assertNotIn('private-test-key',response.text)
        totals=self.client.get('/api/admin/dashboard',headers=self.headers).json()['totals']
        self.assertEqual((totals['results'],totals['ai_success'],totals['ai_errors']),(0,1,1))

    def test_duplicate_email_and_wrong_login(self):
        self.assertEqual(self.client.post("/api/auth/register", json={"name":"Duplicate", "email":"ADMIN@example.test","password":"Test-password-123"}).status_code, 409)
        self.assertEqual(self.client.post("/api/auth/login", json={"email":"admin@example.test","password":"wrong"}).status_code, 401)

    def test_logout_revokes_token(self):
        self.assertEqual(self.client.post("/api/auth/logout", headers=self.student_headers).status_code, 204)
        self.assertEqual(self.client.get("/api/me", headers=self.student_headers).status_code, 401)

    def test_lock_and_role_change_revoke_sessions_and_are_audited(self):
        uid = self.student["user"]["id"]
        path = f"/api/admin/users/{uid}"
        self.assertEqual(self.client.patch(path, json={"role":"student","is_active":False,"version":1}, headers=self.headers).status_code, 200)
        self.assertEqual(self.client.get("/api/me", headers=self.student_headers).status_code, 401)
        self.assertEqual(self.client.post("/api/auth/login", json={"email":"student@example.test","password":"Test-password-123"}).status_code, 403)
        self.client.patch(path, json={"role":"admin","is_active":True,"version":2}, headers=self.headers)
        new_session = self.client.post("/api/auth/login", json={"email":"student@example.test","password":"Test-password-123"}).json()
        new_headers = {"Authorization":"Bearer " + new_session["token"]}
        self.assertEqual(self.client.get("/api/admin/dashboard", headers=new_headers).status_code, 200)
        self.client.patch(path, json={"role":"student","is_active":True,"version":3}, headers=self.headers)
        self.assertEqual(self.client.get("/api/admin/dashboard", headers=new_headers).status_code, 401)
        logs = self.client.get("/api/admin/audit-logs", headers=self.headers).json()
        self.assertEqual(len(logs), 3)
        self.assertNotIn("password_hash", str(logs))
        self.assertNotIn(self.admin["token"], str(logs))

    def test_self_lock_is_rejected_and_user_filters_work(self):
        uid = self.admin["user"]["id"]
        self.assertEqual(self.client.patch(f"/api/admin/users/{uid}", json={"role":"student","is_active":False,"version":1}, headers=self.headers).status_code, 400)
        rows=self.client.get("/api/admin/users?search=Nguyên&role=admin&active=true", headers=self.headers).json()
        self.assertEqual([r["id"] for r in rows], [uid])
        self.assertNotIn("salt", rows[0])

    def test_vocabulary_crud_validation_and_concurrent_edit(self):
        word = self.word()
        body = {k:v for k,v in word.items() if k not in ("id","version")}
        self.assertEqual(self.post("/vocabulary", body).status_code, 409)
        body["hanzi"]="二"
        body["strokes"]=[[{"x":-1,"y":0},{"x":10,"y":10}]]
        self.assertEqual(self.post("/vocabulary", body).status_code, 422)
        body["strokes"]=[]
        body["meaning"]="hai"
        body["version"]=word["version"]
        path=f"/api/admin/vocabulary/{word['id']}"
        updated=self.client.put(path, headers=self.headers, json=body)
        self.assertEqual(updated.status_code, 200, updated.text)
        self.assertEqual(self.client.put(path, headers=self.headers, json=body).status_code, 409)
        self.assertEqual(self.client.get("/api/vocabulary?search=hai").json()[0]["hanzi"], "二")
        self.assertEqual(self.client.delete(path+"?version=1", headers=self.headers).status_code, 409)
        self.assertEqual(self.client.delete(path+"?version=2", headers=self.headers).status_code, 204)

    def test_word_in_exam_cannot_be_deleted(self):
        word=self.word()
        exam=self.exam(word)
        path=f"/api/admin/vocabulary/{word['id']}?version=1"
        self.assertEqual(self.client.delete(path, headers=self.headers).status_code, 409)
        self.assertEqual(self.client.delete(f"/api/admin/exams/{exam['id']}?version=1", headers=self.headers).status_code, 204)
        self.assertEqual(self.client.delete(path, headers=self.headers).status_code, 204)

    def test_exam_answers_are_hidden_and_scores_come_from_server(self):
        exam=self.exam()
        learner_exam=self.client.get("/api/exams", headers=self.student_headers).json()[0]
        for key in ("answer","explanation","transcript"):
            self.assertNotIn(key, learner_exam["questions"][0])
        response=self.client.post(f"/api/exams/{exam['id']}/submit", headers=self.student_headers,
                                  json={"version":1,"answers":{"q1":"hai"},"score":100})
        self.assertEqual(response.status_code, 422)
        with patch('main.grade_reading_exam', return_value={"score": 100, "feedback": "Mock"}):
            result=self.submit(exam,"một")
            self.assertEqual(result["score"], 100)
        self.assertEqual(self.client.delete(f"/api/admin/exams/{exam['id']}?version=1", headers=self.headers).status_code, 409)

    def test_listening_exam_is_graded_by_ai_and_saved(self):
        exam = self.exam(section="listening")
        with patch('main.grade_listening_exam', return_value={
                "score": 88,
                "feedback": "Nghe tốt.",
                "review_items": [{"id": "q1", "explanation": "Transcript có từ 一; đáp án hai là nhiễu."}],
        }) as grader:
            result = self.submit(exam, "một")
        grader.assert_called_once()
        self.assertEqual(result["score"], 88)
        self.assertEqual(result["feedback"], "Nghe tốt.")
        self.assertEqual(result["graded_by"], "ai")
        snapshot = json.loads(result["content"])
        self.assertEqual(snapshot["ai_review_items"][0]["id"], "q1")

    def test_draft_hidden_and_stale_exam_are_not_submitted(self):
        exam=self.exam(status="draft")
        self.assertEqual(self.client.get("/api/exams", headers=self.student_headers).json(), [])
        path=f"/api/exams/{exam['id']}/submit"
        self.assertEqual(self.client.post(path, headers=self.student_headers,json={"version":1,"answers":{"q1":"một"}}).status_code,404)
        body={k:v for k,v in exam.items() if k!="id"}
        body["status"]="published"
        self.assertEqual(self.client.put(f"/api/admin/exams/{exam['id']}",headers=self.headers,json=body).status_code,200)
        self.assertEqual(self.client.post(path, headers=self.student_headers,json={"version":1,"answers":{"q1":"một"}}).status_code,409)

    def test_exam_validation_rejects_missing_audio_duplicates_and_missing_word(self):
        exam=self.exam()
        body={k:v for k,v in exam.items() if k not in ("id","version")}
        body["questions"][0]["section"]="listening"
        self.assertEqual(self.post("/exams",body).status_code,422)
        body["questions"][0]["section"]="reading"
        body["questions"].append(body["questions"][0])
        self.assertEqual(self.post("/exams",body).status_code,422)
        body["questions"].pop()
        body["questions"][0]["word_id"]=9999
        self.assertEqual(self.post("/exams",body).status_code,404)

    def test_score_override_updates_student_dashboard_and_history(self):
        with patch('main.grade_reading_exam', return_value={"score": 0, "feedback": "Mock"}):
            result=self.submit(self.exam())
        path=f"/api/admin/results/{result['id']}/score"
        body={"score":85,"reason":"Đối chiếu lại bài làm theo đáp án chuẩn","version":1}
        self.assertEqual(self.client.patch(path,headers=self.student_headers,json=body).status_code,403)
        self.assertEqual(self.client.patch(path,headers=self.headers,json={**body,"reason":""}).status_code,422)
        self.assertEqual(self.client.patch(path,headers=self.headers,json={**body,"score":101}).status_code,422)
        self.assertEqual(self.client.patch(path,headers=self.headers,json=body).status_code,200)
        self.assertEqual(self.client.patch(path,headers=self.headers,json=body).status_code,409)
        rows=self.client.get("/api/me/results",headers=self.student_headers).json()
        self.assertEqual(rows[0]["score"],85)
        self.assertEqual(rows[0]["original_score"],0)
        self.assertEqual(rows[0]["overrides"][0]["old_score"],0)
        dashboard=self.client.get("/api/me/dashboard",headers=self.student_headers).json()
        self.assertEqual(dashboard["results"], 1)
        self.assertEqual(dashboard["average_score"], 85.0)
        self.assertEqual(dashboard["needs_review"], 0)
        self.assertEqual(dashboard["skill_scores"]["reading"], 85.0)
        self.assertEqual(self.client.get("/api/me/results",headers=self.headers).json(),[])

    def test_ai_config_keeps_key_private_and_checks_version(self):
        body={"model":"test-model","system_prompt":"Chấm điểm 0–100","temperature":0.2,"max_tokens":1000,"enabled":True,"version":1}
        with patch.dict(os.environ,{"GEMINI_API_KEY":"","AI_API_KEY":""}):
            self.assertEqual(self.client.put("/api/admin/ai-config",headers=self.headers,json=body).status_code,422)
        with patch.dict(os.environ,{"GEMINI_API_KEY":"private-test-secret","AI_API_KEY":"private-test-secret"}):
            response=self.client.put("/api/admin/ai-config",headers=self.headers,json=body)
            self.assertEqual(response.status_code,200)
            self.assertTrue(response.json()["ready"])
            self.assertNotIn("private-test-secret",response.text)
            self.assertEqual(self.client.put("/api/admin/ai-config",headers=self.headers,json=body).status_code,409)
            logs=self.client.get("/api/admin/audit-logs",headers=self.headers)
            self.assertNotIn("private-test-secret",logs.text)

    def test_ai_integration_records_real_results_and_sanitizes_failures(self):
        with patch.dict(os.environ,{"GEMINI_API_KEY":"private-test-secret","AI_API_KEY":"private-test-secret"}):
            self.client.put("/api/admin/ai-config",headers=self.headers,json={"model":"test-model","system_prompt":"Chấm bài","temperature":0.2,"max_tokens":1000,"enabled":True,"version":1})
            def provider(settings,content):
                self.assertEqual(settings["api_key"],"private-test-secret")
                return {"score":70,"feedback":"Cần cải thiện ngữ pháp"}
            result=grade_with_ai(self.student["user"]["id"],"writing","我学习汉语。",provider)
            self.assertEqual(result["graded_by"],"ai")
            def broken(settings,content):
                raise RuntimeError("Provider failed: private-test-secret")
            with self.assertRaises(HTTPException) as error:
                grade_with_ai(self.student["user"]["id"],"writing","我的作文",broken)
            self.assertEqual(error.exception.status_code,502)
            self.assertNotIn("private-test-secret",error.exception.detail)
            def provider_http_error(settings,content):
                raise HTTPException(401,"private-test-secret")
            with self.assertRaises(HTTPException) as provider_error:
                grade_with_ai(self.student["user"]["id"],"writing","我的作文",provider_http_error)
            self.assertEqual(provider_error.exception.status_code,502)
            self.assertNotIn("private-test-secret",provider_error.exception.detail)
            with self.assertRaises(HTTPException):
                grade_with_ai(self.student["user"]["id"],"writing","我的作文",lambda *_:{"score":float('nan'),"feedback":"invalid"})
        dashboard=self.client.get("/api/admin/dashboard",headers=self.headers).json()["totals"]
        self.assertEqual(dashboard["ai_success"],1)
        self.assertEqual(dashboard["ai_errors"],3)
        self.assertEqual(dashboard["results"],1)

    def test_dictionary_history_is_private_and_updates_lookup_count(self):
        word = self.word()
        path = f"/api/me/dictionary-history/{word['id']}"
        first = self.client.post(path, headers=self.student_headers, json={"query": "yi"})
        self.assertEqual(first.status_code, 201, first.text)
        second = self.client.post(path, headers=self.student_headers, json={"query": "一"})
        self.assertEqual(second.json()["lookup_count"], 2)
        history = self.client.get("/api/me/dictionary-history", headers=self.student_headers).json()
        self.assertEqual([item["hanzi"] for item in history], ["一"])
        self.assertEqual(self.client.get("/api/me/dictionary-history", headers=self.headers).json(), [])

    def test_writing_below_80_can_be_resubmitted_until_completed(self):
        with storage.database() as conn:
            conn.execute("UPDATE ai_config SET enabled=1,model='test-model'")
        with patch.dict(os.environ, {"GEMINI_API_KEY": "private-test-secret"}), \
             patch('main.gemini_provider', side_effect=[
                 {"score": 60, "feedback": "Cần sửa ngữ pháp."},
                 {"score": 70, "feedback": "Vẫn cần sửa cách dùng từ."},
                 {"score": 85, "feedback": "Bài đã rõ ràng hơn."},
             ]):
            original = self.client.post("/api/writing/submit", headers=self.student_headers,
                                        json={"content": "我学习中文。"})
            self.assertEqual(original.status_code, 201, original.text)
            weak = self.client.get("/api/me/review-items?kind=writing", headers=self.student_headers).json()
            self.assertEqual(len(weak), 1)
            retry = self.client.post(f"/api/me/review/writing/{original.json()['id']}",
                                     headers=self.student_headers,
                                     json={"content": "我每天学习中文。"})
            self.assertEqual(retry.status_code, 201, retry.text)
            self.assertFalse(retry.json()["review_completed"])
            weak = self.client.get("/api/me/review-items?kind=writing",
                                   headers=self.student_headers).json()
            self.assertEqual(len(weak), 1)
            self.assertEqual(weak[0]["latest_result"]["score"], 70)
            retry = self.client.post(f"/api/me/review/writing/{original.json()['id']}",
                                     headers=self.student_headers,
                                     json={"content": "我每天认真学习中文。"})
            self.assertEqual(retry.status_code, 201, retry.text)
            self.assertTrue(retry.json()["review_completed"])
        self.assertEqual(self.client.get("/api/me/review-items?kind=writing",
                                         headers=self.student_headers).json(), [])
        dashboard = self.client.get("/api/me/dashboard", headers=self.student_headers).json()
        self.assertEqual(dashboard["needs_review"], 0)
        self.assertEqual(dashboard["skill_scores"]["writing"], 85)

        # Nguyen's correction must reopen Kiet's completed review, then an
        # appeal restoring the score must complete it again in the same transaction.
        result_id = retry.json()["id"]
        correction = self.client.patch(f"/api/admin/results/{result_id}/score",
            headers=self.headers, json={"score": 65, "reason": "Review correction", "version": 1})
        self.assertEqual(correction.status_code, 200, correction.text)
        self.assertEqual(len(self.client.get("/api/me/review-items?kind=writing",
            headers=self.student_headers).json()), 1)
        self.assertEqual(self.client.get("/api/me/dashboard", headers=self.student_headers).json()["needs_review"], 1)
        appeal = self.client.post(f"/api/me/results/{result_id}/appeals",
            headers=self.student_headers, json={"reason": "Please review this correction"}).json()
        resolved = self.client.patch(f"/api/admin/appeals/{appeal['id']}", headers=self.headers,
            json={"version": 1, "result_version": 2, "score": 90, "response": "Confirmed passing score"})
        self.assertEqual(resolved.status_code, 200, resolved.text)
        self.assertEqual(self.client.get("/api/me/review-items?kind=writing", headers=self.student_headers).json(), [])
        self.assertEqual(self.client.get("/api/me/dashboard", headers=self.student_headers).json()["skill_scores"]["writing"], 90)

    def test_capability_report_uses_skill_scores_and_cache(self):
        with patch('main.grade_reading_exam', return_value={"score": 90, "feedback": "Tốt"}):
            self.submit(self.exam(), "một")
        with storage.database() as conn:
            conn.execute("UPDATE ai_config SET enabled=1,model='test-model'")
        report = {"feedback": "Đọc là điểm mạnh.", "strengths": ["Đọc hiểu tốt"],
                  "improvements": ["Luyện nghe thêm"]}
        with patch.dict(os.environ, {"GEMINI_API_KEY": "private-test-secret"}), \
             patch('main.gemini_capability_provider', return_value=report) as provider:
            first = self.client.get("/api/me/capability", headers=self.student_headers)
            second = self.client.get("/api/me/capability", headers=self.student_headers)
        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(first.json()["skill_scores"]["reading"], 90)
        self.assertEqual(first.json()["generated_by"], "ai")
        self.assertEqual(second.json()["generated_by"], "cache")
        provider.assert_called_once()

    def test_handwriting_canvas_result_enters_and_leaves_review_list(self):
        self.word()
        strokes = [[{"x": 100, "y": 500}, {"x": 900, "y": 500}]]
        with storage.database() as conn:
            conn.execute("UPDATE ai_config SET enabled=1,model='test-model'")
        with patch.dict(os.environ, {"GEMINI_API_KEY": "private-test-secret"}), \
             patch('main.gemini_handwriting_provider', side_effect=[
                 {"score": 55, "feedback": "Nét ngang chưa cân đối."},
                 {"score": 90, "feedback": "Nét đã cân đối."},
             ]):
            original = self.client.post("/api/handwriting/submit", headers=self.student_headers,
                                        json={"target": "一", "strokes": strokes})
            self.assertEqual(original.status_code, 201, original.text)
            weak = self.client.get("/api/me/review-items?kind=handwriting",
                                   headers=self.student_headers).json()
            self.assertEqual(len(weak), 1)
            wrong_target = self.client.post(
                f"/api/me/review/handwriting/{original.json()['id']}",
                headers=self.student_headers, json={"target": "二", "strokes": strokes})
            self.assertEqual(wrong_target.status_code, 422)
            retry = self.client.post(
                f"/api/me/review/handwriting/{original.json()['id']}",
                headers=self.student_headers, json={"target": "一", "strokes": strokes})
            self.assertEqual(retry.status_code, 201, retry.text)
            self.assertTrue(retry.json()["review_completed"])
        self.assertEqual(self.client.get("/api/me/review-items?kind=handwriting",
                                         headers=self.student_headers).json(), [])

    def test_comprehensive_exam_saves_each_skill_score(self):
        body = {
            "title": "HSK 1 tổng hợp", "hsk": 1, "status": "published",
            "duration_minutes": 30,
            "questions": [
                {"id": "l1", "section": "listening", "prompt": "Nghe và chọn",
                 "options": ["một", "hai"], "answer": "một",
                 "audio_url": "https://example.test/audio.mp3", "transcript": "一"},
                {"id": "r1", "section": "reading", "prompt": "一 nghĩa là gì?",
                 "options": ["một", "hai"], "answer": "một"},
                {"id": "w1", "section": "writing", "prompt": "Viết câu với 一",
                 "options": [], "answer": "Rubric: đúng ngữ pháp và có chữ 一"},
            ],
        }
        exam = self.post("/exams", body).json()
        grade = {"score": 80, "feedback": "Khá tốt", "review_items": [],
                 "section_scores": {"listening": 90, "reading": 80, "writing": 70}}
        with patch('main.grade_comprehensive_exam', return_value=grade):
            response = self.client.post(
                f"/api/exams/{exam['id']}/submit", headers=self.student_headers,
                json={"version": exam["version"],
                      "answers": {"l1": "một", "r1": "một", "w1": "我有一个朋友。"}},
            )
        self.assertEqual(response.status_code, 201, response.text)
        snapshot = json.loads(response.json()["content"])
        self.assertEqual(snapshot["section_scores"]["writing"], 70)
        dashboard = self.client.get("/api/me/dashboard", headers=self.student_headers).json()
        self.assertEqual(dashboard["skill_scores"]["listening"], 90)
        self.assertEqual(dashboard["skill_scores"]["reading"], 80)
        self.assertEqual(dashboard["skill_scores"]["writing"], 70)

    def test_ai_contract_rejects_invalid_grades_without_saving_results(self):
        invalid = [
            {"score": True, "feedback": "Nhận xét"},
            {"score": "80", "feedback": "Nhận xét"},
            {"score": 80, "feedback": "   "},
            {"score": 80, "feedback": ""},
            {"score": 101, "feedback": "Nhận xét"},
        ]
        with patch.dict(os.environ, {"AI_API_KEY": "private-test-secret"}):
            self.client.put("/api/admin/ai-config", headers=self.headers, json={
                "model": "test-model", "system_prompt": "Chấm bài", "temperature": 0.2,
                "max_tokens": 1000, "enabled": True, "version": 1})
            for output in invalid:
                with self.subTest(output=output), self.assertRaises(HTTPException) as error:
                    grade_with_ai(self.student["user"]["id"], "writing", "我的作文", lambda *_: output)
                self.assertEqual(error.exception.status_code, 502)
        totals = self.client.get("/api/admin/dashboard", headers=self.headers).json()["totals"]
        self.assertEqual(totals["results"], 0)
        self.assertEqual(totals["ai_success"], 0)
        self.assertEqual(totals["ai_errors"], len(invalid))

    def test_listening_demo_is_visible_playable_and_preserves_admin_edits(self):
        from listening_demo import seed_listening
        seed_listening(publish=True)
        seed_listening(publish=True)
        exams = self.client.get('/api/exams', headers=self.student_headers).json()
        self.assertEqual(len(exams), 3)
        for exam in exams:
            question = exam['questions'][0]
            self.assertEqual(question['section'], 'listening')
            self.assertNotIn('answer', question)
            self.assertNotIn('transcript', question)
            response = self.client.get(question['audio_url'])
            self.assertEqual(response.status_code, 200)
            self.assertIn('audio/', response.headers['content-type'])
            self.assertGreater(len(response.content), 1000)
        admin_exam = self.client.get('/api/admin/exams', headers=self.headers).json()[0]
        body = {k: v for k, v in admin_exam.items() if k != 'id'}
        body['status'] = 'hidden'
        self.assertEqual(self.client.put(f"/api/admin/exams/{admin_exam['id']}",
            headers=self.headers, json=body).status_code, 200)
        seed_listening(publish=True)
        self.assertEqual(len(self.client.get('/api/exams', headers=self.student_headers).json()), 2)
        self.assertEqual(self.client.get('/api/me/results', headers=self.student_headers).json(), [])

    def test_local_audio_validation_rejects_other_paths(self):
        from models import Word
        for value in ['/media/../main.py', '//example.test/a.mp3', '/admin/assets/app.js']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                Word.valid_url(value)

    def test_seed_is_idempotent_and_dashboard_has_no_fake_activity(self):
        seed()
        seed()
        data=self.client.get("/api/admin/dashboard",headers=self.headers).json()["totals"]
        self.assertEqual(data["vocabulary"],8)
        self.assertEqual(data["exams"],7)
        self.assertEqual(data["results"],0)
        self.assertEqual(data["ai_success"],0)
        self.assertEqual(data["average_score"],0)


if __name__ == "__main__":
    unittest.main()
