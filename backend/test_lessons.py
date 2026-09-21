"""Lesson coverage, server grading and isolated per-account progress."""
from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient
import database as storage
from main import app
from lesson_catalog import curriculum


class LessonCatalogTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old = storage.DB_PATH
        storage.DB_PATH = Path(self.temp.name) / 'lessons.db'
        self.client = TestClient(app)
        self.client.__enter__()
        session = self.client.post('/api/auth/register', json={
            'name': 'Learner', 'email': 'lesson@example.test', 'password': 'lesson-test-password'}).json()
        self.headers = {'Authorization': 'Bearer ' + session['token']}
        self.lesson = curriculum()['lessons'][0]
        self.answers = {q['id']: q['answer'] for q in self.lesson['questions']}
        self.path = '/api/me/lessons/' + self.lesson['id']

    def tearDown(self):
        self.client.__exit__(None, None, None)
        storage.DB_PATH = self.old
        self.temp.cleanup()

    def test_original_content_is_complete_and_levelled(self):
        lessons = curriculum()['lessons']
        self.assertEqual(len({l['id'] for l in lessons}), 48)
        self.assertEqual(len({l['title'] for l in lessons}), 48)
        for level in range(1, 7):
            rows = [l for l in lessons if l['hsk'] == level]
            self.assertEqual([l['order'] for l in rows], list(range(1, 9)))
            self.assertTrue(rows[-1]['review'])
            for lesson in rows:
                self.assertEqual(len(lesson['vocabulary']), 5)
                self.assertEqual(len(lesson['questions']), 4)
                self.assertTrue(lesson['grammar']['example']['pinyin'])
                self.assertTrue(lesson['task'])
                self.assertGreaterEqual(len(lesson['reading']['hanzi']), 20)
                for q in lesson['questions']:
                    self.assertEqual(len(set(q['options'])), 3)
                    self.assertIn(q['answer'], range(3))
                    self.assertTrue(q['explanation'])
        self.assertGreater(sum(len(l['reading']['hanzi']) for l in lessons if l['hsk'] == 6),
                           sum(len(l['reading']['hanzi']) for l in lessons if l['hsk'] == 1) * 3)

    def test_public_catalog_filters_and_hides_answers(self):
        self.assertEqual(self.client.get('/api/lessons').json()['total'], 48)
        for level in range(1, 7):
            rows = self.client.get('/api/lessons', params={'hsk': level}).json()['items']
            self.assertEqual(len(rows), 8)
            self.assertTrue(all(r['hsk'] == level for r in rows))
        self.assertEqual(self.client.get('/api/lessons', params={'search': 'chao hoi'}).json()['total'], 1)
        self.assertEqual(self.client.get('/api/lessons', params={'search': 'khongtontai'}).json()['items'], [])
        for q in self.client.get('/api/lessons/hsk1-01').json()['questions']:
            self.assertNotIn('answer', q)
            self.assertNotIn('explanation', q)
        self.assertEqual(self.client.get('/api/lessons/unknown').status_code, 404)
        self.assertEqual(self.client.get('/api/lessons?hsk=7').status_code, 422)

    def test_checkpoints_are_private_and_cannot_forge_completion(self):
        self.assertEqual(self.client.get('/api/me/lessons').status_code, 401)
        self.assertEqual(self.client.put(self.path + '/progress', json={'stage': 1}).status_code, 401)
        for stage in (2, 1, 3):
            r = self.client.put(self.path + '/progress', json={'stage': stage}, headers=self.headers)
            self.assertEqual(r.status_code, 200)
            self.assertGreaterEqual(r.json()['stage'], stage)
        for body in ({'stage': 4}, {'stage': True}, {'stage': 2, 'best_score': 100}):
            self.assertEqual(self.client.put(self.path + '/progress', json=body, headers=self.headers).status_code, 422)
        self.assertEqual(self.client.put('/api/me/lessons/unknown/progress', json={'stage': 1}, headers=self.headers).status_code, 404)
        other = self.client.post('/api/auth/register', json={'name': 'Other', 'email': 'other@example.test', 'password': 'lesson-test-password'}).json()
        self.assertEqual(self.client.get('/api/me/lessons', headers={'Authorization': 'Bearer '+other['token']}).json(), [])
        # Survives a fresh API client session, not a UI-only percentage.
        with TestClient(app) as second:
            self.assertEqual(second.get('/api/me/lessons', headers=self.headers).json()[0]['stage'], 3)

    def test_grading_threshold_retry_preserves_best_and_completion(self):
        wrong = {q['id']: (q['answer'] + 1) % 3 for q in self.lesson['questions']}
        r = self.client.post(self.path+'/submit', json={'answers': wrong}, headers=self.headers)
        self.assertEqual(r.json()['score'], 0)
        self.assertFalse(r.json()['passed'])
        self.assertIsNone(r.json()['progress']['completed_at'])
        partial = {**self.answers, 'q1': wrong['q1']}
        r = self.client.post(self.path+'/submit', json={'answers': partial}, headers=self.headers)
        self.assertEqual(r.json()['score'], 75)
        self.assertTrue(r.json()['passed'])
        self.assertEqual(r.json()['progress']['stage'], 4)
        completed_at = r.json()['progress']['completed_at']
        self.client.post(self.path+'/submit', json={'answers': self.answers}, headers=self.headers)
        r = self.client.post(self.path+'/submit', json={'answers': wrong}, headers=self.headers)
        self.assertEqual(r.json()['progress']['best_score'], 100)
        self.assertEqual(r.json()['progress']['stage'], 4)
        self.assertEqual(r.json()['progress']['completed_at'], completed_at)
        self.assertEqual(r.json()['progress']['attempts'], 4)
        self.client.put(self.path+'/progress', json={'stage': 1}, headers=self.headers)
        self.assertEqual(self.client.get('/api/me/lessons', headers=self.headers).json()[0]['stage'], 4)

    def test_invalid_attempts_do_not_write_progress(self):
        self.assertEqual(self.client.post(self.path+'/submit', json={'answers': self.answers}).status_code, 401)
        for answers in ({}, {**self.answers, 'q1': -1}, {**self.answers, 'q1': 3},
                        {**self.answers, 'q1': True}, {**self.answers, 'q1': '0'},
                        {'q1': 0, 'q2': 0, 'q3': 0, 'unknown': 0}):
            self.assertEqual(self.client.post(self.path+'/submit', json={'answers': answers}, headers=self.headers).status_code, 422)
        self.assertEqual(self.client.post(self.path+'/submit', json={'answers': self.answers, 'score': 100}, headers=self.headers).status_code, 422)
        self.assertEqual(self.client.get('/api/me/lessons', headers=self.headers).json(), [])


if __name__ == '__main__':
    unittest.main()
