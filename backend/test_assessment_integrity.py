"""Regression tests: no invented grades, no leaked keys, no default-admin reset."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

import database as storage
from main import app, hash_password
from assessment_quality import transcript_feedback, reading_assessment_metadata
from services import recognize_handwriting_with_ai
from ai_reading import evaluate_pronunciation_with_gemini


class AssessmentIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_db = storage.DB_PATH
        storage.DB_PATH = Path(self.temp.name) / 'test.db'
        self.client = TestClient(app)
        self.client.__enter__()
        result = self.client.post('/api/auth/register', json={
            'name': 'Learner', 'email': 'learner@example.test', 'password': 'Test-password-123'})
        self.assertEqual(result.status_code, 201, result.text)
        self.uid = result.json()['user']['id']
        self.headers = {'Authorization': 'Bearer ' + result.json()['token']}

    def tearDown(self):
        self.client.__exit__(None, None, None)
        storage.DB_PATH = self.old_db
        self.temp.cleanup()

    def test_text_and_audio_fallback_never_create_acoustic_scores(self):
        for spoken in ('', '你好'):
            data = transcript_feedback('你好', spoken, 'ni3 hao3', 'ni3 hao3', has_audio=True)
            self.assertFalse(data['score_eligible'])
            for key in ('accuracy_percent', 'tone_score', 'phoneme_score', 'fluency_score'):
                self.assertIsNone(data[key])
        self.assertEqual(transcript_feedback('你好', '', has_audio=True)['spoken_recognized'], '')

    def test_audio_provider_requires_attachment_and_valid_scores(self):
        args = dict(user_id=0, target_hanzi='你好', target_pinyin='nǐ hǎo', target_meaning='Xin chào')
        with patch('ai_reading._post_gemini') as provider:
            self.assertIsNone(evaluate_pronunciation_with_gemini(**args, spoken_text='你好'))
            provider.assert_not_called()
        settings = {'model': 'test', 'api_key': 'test'}
        outputs = [{'assessment_status': 'unavailable', 'accuracy_percent': 90},
                   {'assessment_status': 'assessed', 'accuracy_percent': True},
                   {'assessment_status': 'assessed', 'accuracy_percent': float('nan')},
                   {'assessment_status': 'assessed', 'accuracy_percent': 101},
                   {'assessment_status': 'assessed', 'accuracy_percent': 80, 'tone_score': -1}]
        with patch('ai_reading.ai_settings', return_value=settings), patch('ai_reading._post_gemini') as provider:
            for output in outputs:
                with patch('ai_reading._decode_gemini_candidate', return_value=output):
                    self.assertIsNone(evaluate_pronunciation_with_gemini(**args, audio_base64='YXVkaW8='))
            with patch('ai_reading._decode_gemini_candidate', return_value={
                'assessment_status': 'assessed', 'accuracy_percent': 0, 'tone_score': 0}):
                result = evaluate_pronunciation_with_gemini(**args, audio_base64='YXVkaW8=')
            self.assertEqual(provider.call_args.kwargs['json']['contents'][0]['parts'][0]['inlineData']['data'], 'YXVkaW8=')
            self.assertTrue(result['score_eligible'])
            self.assertEqual(result['tone_score'], 0)
            self.assertIsNone(result['phoneme_score'])

    def test_production_otp_unavailable_does_not_create_codes_or_report_success(self):
        with patch.dict(os.environ, {'VERCEL': '1'}), patch('main.smtp_is_configured', return_value=False), \
             patch('main.send_verification_email') as delivery:
            register = self.client.post('/api/auth/register-request', json={
                'name': 'New learner', 'email': 'new@example.test', 'password': 'Test-password-123'})
            reset = self.client.post('/api/auth/forgot-password-request', json={'email': 'learner@example.test'})
            self.assertEqual(register.status_code, 503)
            self.assertEqual(reset.status_code, 503)
            delivery.assert_not_called()
        with storage.database() as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM verification_codes').fetchone()[0], 0)
        import otp_security
        stamp = otp_security.now()
        for i, result in enumerate((False, RuntimeError('PRIVATE_PROVIDER_ERROR'))):
            with patch('otp_security.now', return_value=stamp+i*61), patch('main.send_verification_email', **({'side_effect': result} if isinstance(result, Exception) else {'return_value': result})):
                response = self.client.post('/api/auth/forgot-password-request', json={'email': 'learner@example.test'})
            self.assertEqual(response.status_code, 503)
            self.assertNotIn('PRIVATE_PROVIDER_ERROR', response.text)

    def test_ocr_provider_failure_or_invalid_output_returns_unavailable(self):
        strokes = [[{'x': 1, 'y': 1}, {'x': 100, 'y': 100}]]
        for output in ({'candidates': []}, {'candidates': [{'hanzi': '一', 'confidence': True}]},
                       {'candidates': [{'hanzi': '一', 'confidence': float('nan')}]},
                       {'candidates': [{'hanzi': '一', 'confidence': 101}]}):
            with patch('services.ai_settings', return_value={'model': 'test', 'api_key': 'test'}), \
                 patch('services.record_ai_usage'), self.assertRaises(HTTPException) as err:
                recognize_handwriting_with_ai(self.uid, strokes, provider=lambda *_: output)
            self.assertEqual(err.exception.status_code, 503)
        with patch('services.ai_settings', return_value={}), patch('services.record_ai_usage'), \
             self.assertRaises(HTTPException) as err:
            recognize_handwriting_with_ai(self.uid, strokes, provider=lambda *_: (_ for _ in ()).throw(TimeoutError()))
        self.assertEqual(err.exception.status_code, 503)

    def test_ocr_valid_candidate_still_works(self):
        with patch('services.ai_settings', return_value={}), patch('services.record_ai_usage'):
            result = recognize_handwriting_with_ai(self.uid, [[{'x': 1, 'y': 1}]],
                provider=lambda *_: {'candidates': [{'hanzi': '一', 'confidence': 92}], 'feedback': '候选'})
        self.assertEqual(result['details']['recognized_hanzi'], '一')
        self.assertEqual(result['score'], 92)

    def test_unavailable_audio_is_not_saved_or_counted(self):
        with patch('ai_reading.evaluate_pronunciation_with_gemini', return_value=None):
            result = self.client.post('/api/reading/evaluate', headers=self.headers, json={
                'target_hanzi': '你好', 'target_pinyin': 'nǐ hǎo',
                'spoken_text': '你好', 'audio_base64': 'invalid-audio', 'save_history': True})
        self.assertEqual(result.status_code, 200, result.text)
        data = result.json()
        self.assertEqual(data['assessment_status'], 'transcript_only')
        self.assertIsNone(data['accuracy_percent'])
        self.assertIsNone(data['history_id'])
        self.assertEqual(self.client.get('/api/me/reading/history', headers=self.headers).json()['total'], 0)
        self.assertEqual(self.client.get('/api/me/review-summary', headers=self.headers).json()['reading'], 0)

    def test_assessed_audio_persists_provenance_and_legacy_history_stays_unverified(self):
        assessment = {'assessment_status': 'assessed', 'assessment_source': 'gemini_audio',
                      'score_eligible': True, 'accuracy_percent': 72.0, 'rating': 'Cần cải thiện',
                      'spoken_recognized': '你好', 'tone_score': 70, 'phoneme_score': 74,
                      'fluency_score': None, 'errors': [], 'corrections': [], 'general_feedback': 'Audio assessment'}
        with patch('ai_reading.evaluate_pronunciation_with_gemini', return_value=assessment):
            result = self.client.post('/api/reading/evaluate', headers=self.headers, json={
                'target_hanzi': '你好', 'target_pinyin': 'nǐ hǎo', 'audio_base64': 'YXVkaW8=', 'save_history': True})
        self.assertEqual(result.status_code, 200, result.text)
        self.assertIsNotNone(result.json()['history_id'])
        with storage.database() as conn:
            conn.execute('''INSERT INTO student_reading_history
                (user_id,hanzi,pinyin,accuracy_percent,rating,feedback_json,created_at)
                VALUES(?, '一', 'yī', 10, 'old fallback', 'not-json', ?)''', (self.uid, int(time.time())))
        history = self.client.get('/api/me/reading/history', headers=self.headers).json()['items']
        legacy = next(r for r in history if r['hanzi'] == '一')
        self.assertEqual(legacy['assessment_status'], 'legacy_unverified')
        self.assertIsNone(legacy['accuracy_percent'])
        self.assertEqual(self.client.get('/api/me/review-summary', headers=self.headers).json()['reading'], 1)
        reviews = self.client.get('/api/me/review-items?kind=reading', headers=self.headers).json()
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0]['score'], 72)

    def test_pending_ai_exam_hides_all_private_fields_but_server_can_grade(self):
        questions = [{'id': 'q1', 'prompt': 'Chọn nghĩa', 'pinyin': '', 'options': ['A. một', 'B. hai'],
                      'answer': 'A. một', 'explanation': 'PRIVATE_EXPLANATION', 'correction': 'PRIVATE_CORRECTION',
                      'rubric': {'answer': 'PRIVATE_NESTED'}, 'debug': 'PRIVATE_DEBUG'}]
        with patch('ai_exam.generate_questions_with_gemini', return_value=questions):
            result = self.client.post('/api/me/ai-exams/generate', headers=self.headers,
                json={'question_count': 1, 'content_type': 'vocabulary'})
        self.assertEqual(result.status_code, 201, result.text)
        exam_id = result.json()['id']
        self.assertNotIn('PRIVATE_', result.text)
        self.assertNotIn('answer', result.json()['questions'][0])
        detail = self.client.get(f'/api/me/ai-exams/{exam_id}', headers=self.headers)
        self.assertNotIn('PRIVATE_', detail.text)
        with storage.database() as conn:
            key = json.loads(conn.execute('SELECT questions_json FROM student_ai_exams WHERE id=?', (exam_id,)).fetchone()[0])
        self.assertEqual(key[0]['answer'], 'A. một')
        submitted = self.client.post(f'/api/me/ai-exams/{exam_id}/submit', headers=self.headers,
                                    json={'answers': {'q1': 'A. một'}})
        self.assertEqual(submitted.status_code, 200, submitted.text)
        self.assertEqual(submitted.json()['score'], 100)
        self.assertEqual(submitted.json()['feedback']['details'][0]['correct_answer'], 'A. một')
        reviewed = self.client.get(f'/api/me/ai-exams/{exam_id}', headers=self.headers).json()
        self.assertEqual(reviewed['questions'][0]['answer'], 'A. một')
        with storage.database() as conn:
            self.assertEqual(conn.execute('SELECT graded_by FROM results WHERE user_id=?', (self.uid,)).fetchone()[0], 'automatic')

    def test_retired_admin_credentials_cannot_keep_or_create_sessions_and_reset_recovers(self):
        with storage.database() as conn:
            conn.execute("UPDATE users SET role='admin' WHERE id=?", (self.uid,))
            old_hash = conn.execute('SELECT password_hash FROM users WHERE id=?', (self.uid,)).fetchone()[0]
        fingerprint = hashlib.sha256(old_hash.encode()).hexdigest()
        with patch('account_security._LEGACY_ADMIN_HASH_FINGERPRINT', fingerprint):
            self.assertEqual(self.client.get('/api/admin/dashboard', headers=self.headers).status_code, 403)
            blocked = self.client.post('/api/auth/admin-login', json={
                'email': 'learner@example.test', 'password': 'Test-password-123'})
            self.assertEqual(blocked.status_code, 403)
            with storage.database() as conn:
                conn.execute('''INSERT INTO verification_codes(email,code,purpose,expires_at,created_at)
                    VALUES('learner@example.test','123456','forgot_password',?,?)''',
                    (int(time.time()) + 600, int(time.time())))
            reset = self.client.post('/api/auth/forgot-password-verify', json={
                'email': 'learner@example.test', 'code': '123456', 'new_password': 'Reset-password-456'})
            self.assertEqual(reset.status_code, 200, reset.text)
            recovered = self.client.post('/api/auth/admin-login', json={
                'email': 'learner@example.test', 'password': 'Reset-password-456'})
            self.assertEqual(recovered.status_code, 200, recovered.text)

    def test_startup_does_not_create_or_promote_default_accounts(self):
        with storage.database() as conn:
            before = [dict(r) for r in conn.execute('SELECT id,email,password_hash,salt,role,is_active FROM users ORDER BY id')]
        with TestClient(app):
            pass
        with storage.database() as conn:
            after = [dict(r) for r in conn.execute('SELECT id,email,password_hash,salt,role,is_active FROM users ORDER BY id')]
        self.assertEqual(after, before)
        self.assertEqual(len(after), 1)

    def test_invalid_or_unverified_metadata_is_never_eligible(self):
        for feedback in ('not-json', '{}', 'null', {'assessment_status': 'assessed'},
                         {'assessment_status': 'assessed', 'assessment_source': 'transcript', 'score_eligible': True}):
            self.assertFalse(reading_assessment_metadata(feedback)['score_eligible'])


if __name__ == '__main__':
    unittest.main()
