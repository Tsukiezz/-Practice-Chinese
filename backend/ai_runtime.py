"""Reusable Gemini connections and a bounded, process-local response cache."""
import atexit
from collections import OrderedDict
from concurrent.futures import Future
from threading import Lock
import time

import httpx

_client = None
_client_lock = Lock()


def gemini_http_post(url, **kwargs):
    global _client
    with _client_lock:
        if _client is None or _client.is_closed:
            # Headers/auth stay per request; keys never become client defaults.
            _client = httpx.Client(follow_redirects=False, limits=httpx.Limits(
                max_connections=40, max_keepalive_connections=10, keepalive_expiry=30))
        client = _client
    return client.post(url, **kwargs)


def close_gemini_client():
    global _client
    with _client_lock:
        client, _client = _client, None
    if client is not None:
        client.close()


atexit.register(close_gemini_client)


def translation_thinking(model):
    """Use the current model's documented fast mode only for translation."""
    model = model.removeprefix('models/')
    if any(modality in model for modality in ('image', 'tts', 'live')):
        return None
    if model.startswith(('gemini-3.5-flash', 'gemini-3.6-flash',
                         'gemini-3.1-flash-lite', 'gemini-3-flash-preview')):
        return {'thinkingLevel': 'MINIMAL'}
    if model.startswith(('gemini-3.7-flash', 'gemini-3.8-flash', 'gemini-4-')):
        return {'thinkingLevel': 'LOW'}
    if model.startswith('gemini-2.5-flash'):
        return {'thinkingBudget': 0}
    return None


class ResponseCache:
    """TTL/LRU cache with single-flight: concurrent equal requests share one call.

    Only successful short strings are retained, in RAM, for at most ten minutes.
    The caller supplies an opaque key including account/guest and config scope.
    """
    def __init__(self, max_entries=128, ttl=600, max_chars=8000, clock=time.monotonic):
        self.max_entries, self.ttl, self.max_chars = max_entries, ttl, max_chars
        self.clock = clock
        self._entries = OrderedDict()
        self._inflight = {}
        self._lock = Lock()

    def get_or_compute(self, key, compute):
        with self._lock:
            now = self.clock()
            for expired in [k for k, (until, _) in self._entries.items() if until <= now]:
                del self._entries[expired]
            cached = self._entries.get(key)
            if cached is not None:
                self._entries.move_to_end(key)
                return cached[1], 'hit'
            pending = self._inflight.get(key)
            owner = pending is None
            if owner:
                pending = self._inflight[key] = Future()
        if not owner:
            return pending.result(timeout=55), 'coalesced'
        try:
            value = compute()
        except BaseException as error:
            with self._lock:
                self._inflight.pop(key, None)
            pending.set_exception(error)
            raise
        with self._lock:
            if isinstance(value, str) and len(value) <= self.max_chars:
                self._entries[key] = (self.clock() + self.ttl, value)
                while len(self._entries) > self.max_entries:
                    self._entries.popitem(last=False)
            self._inflight.pop(key, None)
        pending.set_result(value)
        return value, 'miss'
