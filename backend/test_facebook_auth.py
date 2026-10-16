import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import httpx
from fastapi import HTTPException
from fastapi.testclient import TestClient
from database import database, init_db
from main import app
from facebook_auth import verify_identity


class FacebookTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        for p in [patch('database.DB_PATH', Path(temp.name) / 'auth.db'),
                  patch.dict(os.environ, {'TURSO_DATABASE_URL': '', 'HANZIGO_DB_DRIVER': 'sqlite',
                      'FACEBOOK_APP_ID': '', 'FACEBOOK_APP_SECRET': '', 'FACEBOOK_GRAPH_VERSION': ''})]:
            p.start()
            self.addCleanup(p.stop)
        init_db()
        from usecase_features import init_features
        init_features()
        self.client = TestClient(app)

    def login(self, profile):
        with patch('facebook_auth.verify_identity', return_value=profile):
            return self.client.post('/api/auth/facebook-login', json={'access_token': 'test'})

    def test_disabled(self):
        self.assertEqual(self.client.get('/api/auth/facebook-config').json(),
                         {'enabled': False, 'app_id': '', 'version': ''})
        self.assertEqual(self.client.post('/api/auth/facebook-login', json={'access_token': 'test'}).status_code, 503)

    def test_create_repeat_and_locked(self):
        profile = {'id': '123', 'email': 'fb@example.test', 'name': 'Learner'}
        first = self.login(profile)
        self.assertEqual(first.status_code, 200, first.text)
        user_id = first.json()['user']['id']
        with database() as conn:
            conn.execute('UPDATE users SET name=? WHERE id=?', ('Chosen', user_id))
        second = self.login(profile)
        self.assertEqual(second.json()['user']['name'], 'Chosen')
        self.assertEqual(second.json()['user']['id'], user_id)
        with database() as conn:
            conn.execute('UPDATE users SET is_active=0 WHERE id=?', (user_id,))
        self.assertEqual(self.login(profile).status_code, 403)

    def test_missing_email_and_no_automatic_linking(self):
        self.assertEqual(self.login({'id': '123'}).status_code, 422)
        profile = {'id': '123', 'email': 'fb@example.test', 'name': 'Learner'}
        self.assertEqual(self.login(profile).status_code, 200)
        self.assertEqual(self.login(dict(profile, id='456')).status_code, 409)

    def test_server_verification(self):
        with patch.dict(os.environ, {'FACEBOOK_APP_ID': '123', 'FACEBOOK_APP_SECRET': 'secret',
                                    'FACEBOOK_GRAPH_VERSION': 'v99.0'}):
            self.assertNotIn('secret', self.client.get('/api/auth/facebook-config').text)
            valid = {'is_valid': True, 'app_id': '123', 'user_id': '789', 'type': 'USER',
                     'expires_at': int(time.time()) + 3600}
            for changes in ({}, {'app_id': 'wrong'}, {'expires_at': 1}, {'is_valid': False}):
                with self.subTest(changes=changes), patch('facebook_auth.httpx.Client') as factory:
                    factory.return_value.__enter__.return_value.get.side_effect = [
                        httpx.Response(200, json={'data': dict(valid, **changes)}),
                        httpx.Response(200, json={'id': '789', 'email': 'fb@example.test'})]
                    if changes:
                        with self.assertRaises(HTTPException) as error:
                            verify_identity('test')
                        self.assertEqual(error.exception.status_code, 401)
                    else:
                        self.assertEqual(verify_identity('test')['id'], '789')


if __name__ == '__main__':
    unittest.main()
