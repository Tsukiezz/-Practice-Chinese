import os
import unittest
from unittest.mock import patch
import httpx
from services import _post_gemini
from ai_errors import AIProviderError


class KeyFallbackTest(unittest.TestCase):
    @patch.dict(os.environ, {'GEMINI_FALLBACK_API_KEYS':'backup,backup','GEMINI_FALLBACK_MODEL':''})
    def test_retries_server_key_without_mutating_callers_headers(self):
        for status in [401, 403, 429]:
            sent=[]
            def post(url, **kwargs):
                sent.append(kwargs['headers']['x-goog-api-key'])
                return httpx.Response(status if len(sent)==1 else 200, json={
                    'candidates':[{'content':{'parts':[{'text':'{"answer":"ok"}'}]}}]})
            headers={'x-goog-api-key':'primary'}
            _post_gemini('https://generativelanguage.googleapis.com/v1beta/models/test:generateContent',headers,{},18,post=post,sleep=lambda _:None)
            self.assertEqual(sent,['primary','backup'])
            self.assertEqual(headers['x-goog-api-key'],'primary')

    @patch.dict(os.environ, {'GEMINI_FALLBACK_API_KEYS':'private-backup','GEMINI_FALLBACK_MODEL':''})
    def test_does_not_send_backup_to_another_host(self):
        sent=[]
        def post(url, **kwargs):
            sent.append(kwargs['headers']['x-goog-api-key'])
            return httpx.Response(403)
        with self.assertRaises(AIProviderError):
            _post_gemini('https://example.com/models/test',{'x-goog-api-key':'primary'}, {},18,post=post,sleep=lambda _:None)
        self.assertEqual(sent,['primary'])
