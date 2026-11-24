"""Latency regression tests: pooling, compatible thinking, caching and privacy."""
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from threading import Event, Lock
import tempfile
import unittest
from unittest.mock import Mock, patch

import httpx
from fastapi import HTTPException
from fastapi.testclient import TestClient

import ai_runtime
from ai_runtime import ResponseCache, translation_thinking
import database as storage
from main import app
from services import _post_gemini


def candidate(value='Bản dịch kiểm thử'):
    import json
    return httpx.Response(200, request=httpx.Request('POST', 'https://example.test'), json={
        'candidates': [{'finishReason': 'STOP', 'content': {'parts': [
            {'text': json.dumps({'translation': value})}]}}]})


class RuntimeSpeedTests(unittest.TestCase):
    def test_connections_reused_but_auth_is_per_request_and_shutdown_closes(self):
        ai_runtime.close_gemini_client()
        client = Mock(is_closed=False)
        with patch('ai_runtime.httpx.Client', return_value=client) as factory:
            for key in ('first-key', 'rotated-key'):
                ai_runtime.gemini_http_post('https://example.test', headers={'x-goog-api-key': key})
            factory.assert_called_once()
            self.assertNotIn('headers', factory.call_args.kwargs)
            self.assertEqual(client.post.call_args_list[0].kwargs['headers']['x-goog-api-key'], 'first-key')
            self.assertEqual(client.post.call_args_list[1].kwargs['headers']['x-goog-api-key'], 'rotated-key')
            ai_runtime.close_gemini_client()
            client.close.assert_called_once()

    def test_fast_profile_matches_each_retry_model_and_leaves_input_unchanged(self):
        payload = {'generationConfig': {'maxOutputTokens': 1024}}
        sent = []
        def post(url, **kwargs):
            sent.append(kwargs['json'])
            return httpx.Response(503) if len(sent) == 1 else candidate()
        with patch.dict('os.environ', {'GEMINI_FALLBACK_MODEL': 'gemini-2.5-flash'}):
            response = _post_gemini('https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent',
                {}, payload, 20, post=post, sleep=lambda _: None, latency_profile='translation')
        self.assertEqual(sent[0]['generationConfig']['thinkingConfig'], {'thinkingLevel': 'MINIMAL'})
        self.assertEqual(sent[1]['generationConfig']['thinkingConfig'], {'thinkingBudget': 0})
        self.assertEqual(payload, {'generationConfig': {'maxOutputTokens': 1024}})
        self.assertEqual(response.extensions['hanzigo_ai']['attempts'], 2)

    def test_grading_and_unknown_models_keep_their_reasoning_settings(self):
        post = Mock(return_value=candidate())
        _post_gemini('https://example.test/models/gemini-3.5-flash:generateContent', {}, {}, 20, post=post)
        self.assertNotIn('generationConfig', post.call_args.kwargs['json'])
        for model in ('custom-model', 'gemini-3.1-flash-lite-image', 'gemini-2.5-pro'):
            self.assertIsNone(translation_thinking(model))
        self.assertEqual(translation_thinking('gemini-3.8-flash'), {'thinkingLevel': 'LOW'})

    def test_changed_model_alias_can_retry_without_fast_thinking(self):
        post = Mock(side_effect=[httpx.Response(400), candidate()])
        response = _post_gemini('https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent',
            {}, {}, 20, post=post, latency_profile='translation')
        self.assertIn('thinkingConfig', post.call_args_list[0].kwargs['json']['generationConfig'])
        self.assertNotIn('thinkingConfig', post.call_args_list[1].kwargs['json'].get('generationConfig', {}))
        self.assertEqual(response.extensions['hanzigo_ai']['attempts'], 2)

    def test_cache_expiry_lru_limit_errors_and_large_values(self):
        now = [0]
        cache = ResponseCache(max_entries=2, ttl=10, max_chars=10, clock=lambda: now[0])
        compute = Mock(return_value='ok')
        self.assertEqual(cache.get_or_compute('a', compute)[1], 'miss')
        self.assertEqual(cache.get_or_compute('a', compute)[1], 'hit')
        now[0] = 11
        self.assertEqual(cache.get_or_compute('a', compute)[1], 'miss')
        cache.get_or_compute('b', compute)
        cache.get_or_compute('c', compute)
        self.assertEqual(cache.get_or_compute('a', compute)[1], 'miss')
        bad = Mock(side_effect=ValueError('provider unavailable'))
        for _ in range(2):
            with self.assertRaises(ValueError): cache.get_or_compute('bad', bad)
        self.assertEqual(bad.call_count, 2)
        for _ in range(2): self.assertEqual(cache.get_or_compute('long', lambda: 'x' * 11)[1], 'miss')

    def test_concurrent_identical_requests_only_generate_once(self):
        entered, release, waiting = Event(), Event(), Event()
        counter_lock = Lock()
        counts = {'calls': 0, 'waiters': 0}
        class TrackingFuture(Future):
            def result(self, timeout=None):
                with counter_lock:
                    counts['waiters'] += 1
                    if counts['waiters'] == 2: waiting.set()
                return super().result(timeout)
        def compute():
            counts['calls'] += 1
            entered.set()
            if not release.wait(5): raise TimeoutError()
            return 'shared result'
        cache = ResponseCache()
        with patch('ai_runtime.Future', TrackingFuture), ThreadPoolExecutor(max_workers=3) as pool:
            first = pool.submit(cache.get_or_compute, 'same', compute)
            self.assertTrue(entered.wait(2))
            others = [pool.submit(cache.get_or_compute, 'same', compute) for _ in range(2)]
            try: self.assertTrue(waiting.wait(2))
            finally: release.set()
            values = [first.result(), *(f.result() for f in others)]
        self.assertEqual(counts['calls'], 1)
        self.assertEqual(sorted(status for _, status in values), ['coalesced', 'coalesced', 'miss'])


class TranslationSpeedTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_db = storage.DB_PATH
        storage.DB_PATH = Path(self.temp.name) / 'speed.db'
        self.client = TestClient(app)
        self.client.__enter__()
        self.settings = {'model': 'gemini-3.5-flash', 'api_key': 'test-key', 'version': 1}
        self.cache_patch = patch('translation_service._cache', ResponseCache())
        self.cache_patch.start()
        self.payload = {'text': '我明天还你三本书。', 'source': 'zh', 'target': 'vi'}

    def tearDown(self):
        self.cache_patch.stop()
        self.client.__exit__(None, None, None)
        storage.DB_PATH = self.old_db
        self.temp.cleanup()

    def test_guest_cache_is_private_and_does_not_bypass_rate_limits(self):
        with patch('translation_service.ai_settings', return_value=self.settings), \
             patch('translation_service._post_gemini', side_effect=lambda *a, **k: candidate()) as post:
            first = self.client.post('/api/translation/text', json=self.payload)
            second = self.client.post('/api/translation/text', json=self.payload)
            self.assertEqual(first.status_code, 200, first.text)
            self.assertEqual(second.json(), first.json())
            self.assertEqual(second.headers['x-hanzigo-ai-cache'], 'hit')
            self.assertEqual(second.headers['cache-control'], 'no-store')
            self.assertIn('httponly', first.headers['set-cookie'].lower())
            self.assertIn('server-timing', second.headers)
            other = TestClient(app)
            self.assertEqual(other.post('/api/translation/text', json=self.payload).headers['x-hanzigo-ai-cache'], 'miss')
            self.assertEqual(post.call_count, 2)
            with storage.database() as c:
                c.execute("UPDATE request_limits SET count=20 WHERE key='guest:testclient'")
            self.assertEqual(self.client.post('/api/translation/text', json=self.payload).status_code, 429)
            self.assertEqual(post.call_count, 2)

    def test_cache_invalidates_on_config_and_never_bypasses_disabled_ai(self):
        with patch('translation_service.ai_settings', return_value=self.settings) as settings, \
             patch('translation_service._post_gemini', side_effect=lambda *a, **k: candidate()) as post:
            self.client.post('/api/translation/text', json=self.payload)
            settings.return_value = {**self.settings, 'version': 2}
            self.assertEqual(self.client.post('/api/translation/text', json=self.payload).headers['x-hanzigo-ai-cache'], 'miss')
            self.assertEqual(post.call_count, 2)
            settings.side_effect = HTTPException(503, 'AI disabled')
            self.assertEqual(self.client.post('/api/translation/text', json=self.payload).status_code, 503)

    def test_invalid_output_is_not_cached_and_long_text_keeps_output_budget(self):
        with patch('translation_service.ai_settings', return_value=self.settings), \
             patch('translation_service._post_gemini', side_effect=[candidate(''), candidate('Đúng')]) as post:
            self.assertEqual(self.client.post('/api/translation/text', json=self.payload).status_code, 502)
            self.assertEqual(self.client.post('/api/translation/text', json=self.payload).json(), {'translation': 'Đúng'})
            self.assertEqual(post.call_count, 2)
            self.assertEqual(post.call_args.kwargs['latency_profile'], 'translation')
        with patch('translation_service.ai_settings', return_value=self.settings), \
             patch('translation_service._post_gemini', return_value=candidate()) as post:
            self.client.post('/api/translation/text', json={**self.payload, 'text': '我' * 5000})
            self.assertEqual(post.call_args.kwargs['json']['generationConfig']['maxOutputTokens'], 8192)

    def test_user_direction_and_rotation_scopes_do_not_share_results(self):
        from translation_service import translate_with_ai
        with patch('translation_service.ai_settings', return_value=self.settings), \
             patch('translation_service._post_gemini', side_effect=lambda *a, **k: candidate()) as post:
            for scope, source, target in [('user:1', 'zh', 'vi'), ('user:2', 'zh', 'vi'), ('user:1', 'vi', 'zh')]:
                translate_with_ai('测试', source, target, None, scope)
            self.settings['api_key'] = 'rotated-test-key'
            translate_with_ai('测试', 'zh', 'vi', None, 'user:1')
            self.assertEqual(post.call_count, 4)
