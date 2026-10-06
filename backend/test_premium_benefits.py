import hashlib
import json
import os
import sqlite3
import time
import unittest
import uuid
from datetime import datetime
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient
from database import database, init_db
from main import app
from ai_exam import check_daily_quota, init_ai_exam_tables
from lesson_catalog import init_lessons
from advanced_hsk import exams, lessons
from premium_benefits import LOCAL_TZ, benefits, protected_streak, streak_details
from support_chat import generate_reply, is_on_topic_chinese_or_hanzigo


class PremiumBenefitsTest(unittest.TestCase):
    def setUp(self):
        env = patch.dict(os.environ, {'TURSO_DATABASE_URL': '', 'HANZIGO_DB_DRIVER': 'sqlite',
                                     'SEPAY_MERCHANT_ID': '', 'SEPAY_SECRET_KEY': ''})
        env.start()
        self.addCleanup(env.stop)
        connect = sqlite3.connect
        uri = 'file:benefits-' + uuid.uuid4().hex + '?mode=memory&cache=shared'
        keeper = connect(uri, uri=True)
        self.addCleanup(keeper.close)
        connector = patch('database.sqlite3.connect', side_effect=lambda *a, **kw: connect(uri, uri=True))
        connector.start()
        self.addCleanup(connector.stop)
        init_db()
        init_lessons()
        now = int(time.time())
        with database() as conn:
            init_ai_exam_tables(conn)
            self.uid = conn.execute("INSERT INTO users(name,email,password_hash,salt,role,is_active,created_at) VALUES('Test','benefits@test.local','x','y','student',1,?)", (now,)).lastrowid
            conn.execute('INSERT INTO sessions VALUES(?,?,?)', (hashlib.sha256(b'benefits-test-token').hexdigest(), self.uid, now + 86400))
        self.headers = {'Authorization': 'Bearer benefits-test-token'}
        self.client = TestClient(app)

    def user(self, until=None):
        with database() as conn:
            if until is not None:
                conn.execute('UPDATE users SET premium_until=? WHERE id=?', (until, self.uid))
            return dict(conn.execute('SELECT * FROM users WHERE id=?', (self.uid,)).fetchone())

    def paid(self):
        return self.user(int(time.time()) + 365 * 86400)

    def test_free_and_expired_cannot_access_any_advanced_material(self):
        for until in (0, int(time.time()) - 1):
            self.user(until)
            for level in (7, 8, 9):
                self.assertEqual(self.client.get(f'/api/exams?hsk={level}', headers=self.headers).status_code, 403)
                self.assertEqual(self.client.get(f'/api/lessons/hsk{level}-01', headers=self.headers).status_code, 403)
                self.assertEqual(self.client.put(f'/api/me/lessons/hsk{level}-01/progress', headers=self.headers, json={'stage': 1}).status_code, 403)
                self.assertEqual(self.client.post(f'/api/me/lessons/hsk{level}-01/submit', headers=self.headers, json={'answers': {f'q{i}': 0 for i in range(1,5)}}).status_code, 403)
                self.assertEqual(self.client.post(f'/api/exams/{-(level*100+99)}/submit', headers=self.headers, json={'version': 1, 'answers': {'x': 'x'}}).status_code, 403)
            self.assertEqual(self.client.get('/api/lessons/communication-01', headers=self.headers).status_code, 403)

    def test_guest_cannot_get_advanced_detail(self):
        self.assertEqual(self.client.get('/api/lessons/hsk7-01').status_code, 401)
        self.assertEqual(self.client.get('/api/exams?hsk=7').status_code, 401)
        self.assertEqual(self.client.get('/api/lessons/hsk1-01').status_code, 200)

    def test_paid_all_levels_have_listening_reading_and_mixed_exam(self):
        self.paid()
        for level in (7, 8, 9):
            response = self.client.get(f'/api/exams?hsk={level}', headers=self.headers)
            self.assertEqual(response.status_code, 200, response.text)
            rows = response.json()
            self.assertEqual(len(rows), 5)
            kinds = [{q['section'] for q in e['questions']} for e in rows]
            self.assertIn({'listening'}, kinds)
            self.assertIn({'reading'}, kinds)
            self.assertIn({'reading', 'listening'}, kinds)
            for exam in rows:
                for q in exam['questions']:
                    self.assertNotIn('answer', q)
                    self.assertNotIn('explanation', q)
                    self.assertNotIn('transcript', q)
                    if q['section'] == 'listening':
                        self.assertTrue(q['audio_url'].startswith('/api/tts?text='))

    def test_advanced_grades_and_saves_owned_results(self):
        self.paid()
        for level in (7, 8, 9):
            exam = exams(level)[-1]
            answers = {q['id']: q['answer'] for q in exam['questions']}
            r = self.client.post(f"/api/exams/{exam['id']}/submit", headers=self.headers, json={'version': 1, 'answers': answers})
            self.assertEqual(r.status_code, 201, r.text)
            self.assertEqual(r.json()['score'], 100)
            self.assertEqual(r.json()['user_id'], self.uid)
            snapshot = json.loads(r.json()['content'])
            self.assertEqual(snapshot['section_scores'], {'reading': 100, 'listening': 100})
            with database() as conn:
                self.assertEqual(conn.execute('SELECT user_id FROM results WHERE id=?', (r.json()['id'],)).fetchone()[0], self.uid)
            self.assertEqual(self.client.post(f"/api/exams/{exam['id']}/submit", headers=self.headers, json={'version': 2, 'answers': answers}).status_code, 409)
            answers[next(iter(answers))] = 'forged'
            self.assertEqual(self.client.post(f"/api/exams/{exam['id']}/submit", headers=self.headers, json={'version': 1, 'answers': answers}).status_code, 422)

    def test_advanced_lessons_grade_and_persist_progress(self):
        self.paid()
        for lesson in lessons():
            lid = lesson['id']
            detail = self.client.get(f'/api/lessons/{lid}', headers=self.headers)
            self.assertEqual(detail.status_code, 200)
            self.assertEqual(len(detail.json()['questions']), 4)
            self.assertTrue(all('answer' not in q for q in detail.json()['questions']))
            r = self.client.post(f'/api/me/lessons/{lid}/submit', headers=self.headers,
                                 json={'answers': {q['id']: q['answer'] for q in lesson['questions']}})
            self.assertEqual(r.status_code, 200, r.text)
            self.assertEqual(r.json()['progress']['stage'], 4)
            self.assertEqual(r.json()['score'], 100)
        self.assertEqual(len(self.client.get('/api/me/lessons', headers=self.headers).json()), 7)

    def test_preferences_server_gate_persistence_and_expiry(self):
        path = '/api/me/benefits/preferences'
        self.assertEqual(self.client.put(path, json={'brush': 'brush', 'palette': 'blue'}).status_code, 401)
        self.assertEqual(self.client.put(path, headers=self.headers, json={'brush': 'brush', 'palette': 'blue'}).status_code, 403)
        self.paid()
        self.assertEqual(self.client.put(path, headers=self.headers, json={'brush': 'calligraphy', 'palette': 'purple'}).status_code, 200)
        self.assertEqual(self.client.get('/api/me/benefits', headers=self.headers).json()['brush'], 'calligraphy')
        self.user(0)
        data = self.client.get('/api/me/benefits', headers=self.headers).json()
        self.assertEqual((data['brush'], data['palette'], data['gold_badge']), ('default', 'dark', False))
        self.assertEqual(self.client.put(path, headers=self.headers, json={'brush': 'brush', 'is_premium': True}).status_code, 422)

    def test_streak_uses_three_credits_once_and_resets_by_calendar_month(self):
        now = int(datetime(2026, 10, 5, 12, tzinfo=LOCAL_TZ).timestamp())
        user = self.user(now + 365*86400)
        with database() as conn:
            benefits(conn, user, now - 4*86400)
            days = ['2026-10-01', '2026-10-05']
            self.assertEqual(protected_streak(conn, user, days, now), 5)
            self.assertEqual(protected_streak(conn, user, days, now), 5)
            self.assertEqual(benefits(conn, user, now)['streak_freezes'], 0)
            self.assertEqual(protected_streak(conn, user, days, now+2*86400), 0)
            november = int(datetime(2026, 11, 1, tzinfo=LOCAL_TZ).timestamp())
            self.assertEqual(benefits(conn, user, november)['streak_freezes'], 3)

    def test_dictionary_repeated_word_keeps_previous_day_and_dashboard_is_private(self):
        from ai_reading import init_reading_tables
        with database() as conn:
            init_reading_tables(conn)
            word = conn.execute("INSERT INTO vocabulary(hanzi,pinyin,meaning,hsk,example,audio_url,strokes_json) VALUES('学','xue','learn',1,'','','[]')").lastrowid
        now = int(time.time())
        for timestamp in (now - 86400, now, now):
            with patch('main.time.time', return_value=timestamp):
                response = self.client.post(f'/api/me/dictionary-history/{word}', headers=self.headers, json={'query': '学'})
                self.assertEqual(response.status_code, 201)
        response = self.client.get('/api/me/dashboard', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        details = response.json()['streak_details']
        self.assertEqual(details['total_learning_days'], 2)
        self.assertEqual(details['current'], 2)
        self.assertTrue(details['learned_today'])
        self.assertEqual(self.client.get('/api/me/dashboard').status_code, 401)

    def test_personal_streak_calendar_and_milestone(self):
        now = int(datetime(2026, 10, 5, 0, 5, tzinfo=LOCAL_TZ).timestamp())
        with database() as conn:
            details = streak_details(conn, self.user(), ['2026-10-02', '2026-10-03', '2026-10-04', '2026-10-04'], now)
            self.assertEqual(details['current'], 3)
            self.assertEqual(details['longest'], 3)
            self.assertEqual(details['total_learning_days'], 3)
            self.assertEqual(details['next_milestone'], 7)
            self.assertFalse(details['learned_today'])
            self.assertEqual(len(details['calendar']), 28)
            self.assertEqual(details['calendar'][-1], {'date': '2026-10-05', 'status': 'empty'})
            self.assertEqual(details['calendar'][-2]['status'], 'learned')
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM learner_activity_days WHERE user_id=?', (self.uid,)).fetchone()[0], 0)

    def test_personal_streak_empty_and_frozen_days_are_not_learning(self):
        now = int(datetime(2026, 10, 5, 12, tzinfo=LOCAL_TZ).timestamp())
        user = self.user()
        with database() as conn:
            empty = streak_details(conn, user, [], now)
            self.assertEqual(empty['current'], 0)
            self.assertEqual(empty['longest'], 0)
            conn.execute('INSERT INTO streak_protection(user_id,day) VALUES(?,?)', (self.uid, '2026-10-04'))
            details = streak_details(conn, user, ['2026-10-03', '2026-10-05'], now)
            self.assertEqual(details['current'], 3)
            self.assertEqual(details['longest'], 3)
            self.assertEqual(details['total_learning_days'], 2)
            self.assertTrue(details['learned_today'])
            self.assertEqual(details['calendar'][-2]['status'], 'protected')

    def test_free_streak_yesterday_is_not_lost_before_today_ends(self):
        now = int(datetime(2026, 10, 5, 12, tzinfo=LOCAL_TZ).timestamp())
        with database() as conn:
            self.assertEqual(protected_streak(conn, self.user(), ['2026-10-04'], now), 1)
            self.assertEqual(protected_streak(conn, self.user(), ['2026-10-03'], now), 0)

    def test_freeze_does_not_repair_before_activation(self):
        now = int(datetime(2026, 10, 5, 12, tzinfo=LOCAL_TZ).timestamp())
        user = self.user(now+86400)
        with database() as conn:
            self.assertEqual(protected_streak(conn, user, ['2026-10-01'], now), 0)
            self.assertEqual(benefits(conn, user, now)['streak_freezes'], 3)

    def test_quota_presets_excluded_deletion_does_not_reset_and_midnight_resets(self):
        now = int(datetime(2026, 10, 5, 23, 59, tzinfo=LOCAL_TZ).timestamp())
        user = self.user()
        with database() as conn:
            for i in range(6):
                conn.execute("INSERT INTO student_ai_exams(user_id,title,content_type,question_count,duration_minutes,questions_json,created_at) VALUES(?,'preset','standard_hsk',40,40,'[]',?)", (self.uid, now))
            for _ in range(3):
                check_daily_quota(conn, user, now, consume=True)
            conn.execute('DELETE FROM student_ai_exams WHERE user_id=?', (self.uid,))
            with self.assertRaises(HTTPException) as error:
                check_daily_quota(conn, user, now, consume=True)
            self.assertEqual(error.exception.status_code, 403)
            check_daily_quota(conn, user, now+120, consume=True)

    def test_premium_quota_unlimited_and_advanced_ai_no_beginner_fallback(self):
        user = self.paid()
        with database() as conn:
            for _ in range(10):
                check_daily_quota(conn, user, int(time.time()), consume=True)
        with patch('ai_exam.generate_questions_with_gemini', return_value=None), patch('ai_exam.generate_questions_from_db') as fallback:
            response = self.client.post('/api/me/ai-exams/generate', headers=self.headers, json={'hsk_level': 9, 'question_count': 5})
            self.assertEqual(response.status_code, 503)
            fallback.assert_not_called()

    def test_assistant_accepts_features_and_receives_release_knowledge(self):
        for question in ('Chuỗi ngày học xem ở đâu?', 'Premium có bao nhiêu lượt bảo lưu?', 'SePay chưa nhận tiền', 'Bút lông mở thế nào?', 'HSK 9 có bài nghe không?'):
            self.assertTrue(is_on_topic_chinese_or_hanzigo(question))
        with patch('support_chat.ai_settings', return_value={'api_key': 'unconfigured'}):
            answer, admin = generate_reply([{'role': 'user', 'content': 'Premium có HSK 9 không?'}])
            self.assertIn('HSK 7', answer)
            self.assertFalse(admin)
            answer, admin = generate_reply([{'role': 'user', 'content': 'Chuyển khoản rồi nhưng chưa nhận Premium'}])
            self.assertTrue(admin)
            self.assertIn('không cần chuyển tiền', answer)

    def test_release_knowledge_appends_even_when_admin_has_custom_prompt(self):
        with patch('support_chat.get_chat_ai_config', return_value=('Custom tutor prompt', 'Decline', True)), \
             patch('support_chat.ai_settings', return_value={'model': 'test-model', 'api_key': 'test-only'}), \
             patch('support_chat._post_gemini') as post, \
             patch('support_chat._decode_gemini_candidate', return_value={'answer': 'Thông tin Premium', 'chinese_topic': True, 'needs_admin': False}):
            generate_reply([{'role': 'user', 'content': 'Premium có gì?'}])
            prompt = post.call_args.args[2]['systemInstruction']['parts'][0]['text']
            self.assertIn('Custom tutor prompt', prompt)
            self.assertIn('HSK 7', prompt)
            self.assertIn('3 ngày mỗi tháng lịch', prompt)
            self.assertIn('49,000', prompt)


if __name__ == '__main__':
    unittest.main()
