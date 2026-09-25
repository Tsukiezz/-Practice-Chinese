import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import httpx
from pydantic import ValidationError

from ai_errors import AIProviderError, ai_http_error
from services import _post_gemini, _decode_gemini_candidate
from usecase_features import Translation


class AIReliabilityTest(unittest.TestCase):
    def test_overload_switches_model_with_same_request_and_key(self):
        url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent'
        request = httpx.Request('POST', url)
        payload = {'contents': [{'parts': [{'text': 'grade sample'}]}]}
        responses = [httpx.Response(503, request=request), httpx.Response(200, request=request, json={
            'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': '{"score":80}'}]}}]})]
        with patch.dict(os.environ, {'GEMINI_FALLBACK_MODEL': 'gemini-3.5-flash-lite'}), \
             patch('services.httpx.post', side_effect=responses) as post, patch('services.time.sleep'):
            response = _post_gemini(url, {'x-goog-api-key': 'test-secret'}, payload, 20)
        self.assertEqual(_decode_gemini_candidate(response)['score'], 80)
        self.assertIn('/gemini-3.5-flash-lite:', post.call_args_list[1].args[0])
        self.assertEqual(post.call_args_list[1].kwargs['json'], payload)
        self.assertFalse(post.call_args_list[1].kwargs['follow_redirects'])

    def test_bad_key_is_not_retried_or_disclosed(self):
        response = httpx.Response(403, text='private-test-secret')
        with patch('services.httpx.post', return_value=response) as post:
            with self.assertRaises(AIProviderError) as caught:
                _post_gemini('https://example.test', {}, {}, 10)
        self.assertEqual(post.call_count, 1)
        self.assertEqual(ai_http_error(caught.exception, 'fallback').status_code, 503)
        self.assertNotIn('private-test-secret', str(caught.exception))

    def test_thought_parts_are_ignored_and_text_parts_are_joined(self):
        response = httpx.Response(200, json={'candidates': [{'finishReason': 'STOP', 'content': {'parts': [
            {'thought': True, 'text': 'internal'}, {'text': '{"score":'}, {'text': '90}'}]}}]})
        self.assertEqual(_decode_gemini_candidate(response), {'score': 90})
        response = httpx.Response(200, json={'candidates': [{'finishReason': 'MAX_TOKENS',
            'content': {'parts': [{'text': '{"score":90}'}]}}]})
        with self.assertRaises(ValueError):
            _decode_gemini_candidate(response)

    def test_translation_accepts_only_chinese_and_vietnamese(self):
        for source, target in [('zh', 'vi'), ('vi', 'zh')]:
            self.assertEqual(Translation(text='test', source=source, target=target).target, target)
        for language in ['en', 'ja', 'ko', 'fr']:
            with self.assertRaises(ValidationError):
                Translation(text='test', source=language)
            with self.assertRaises(ValidationError):
                Translation(text='test', target=language)
