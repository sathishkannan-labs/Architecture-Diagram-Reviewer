"""Controls for the single-process public preview; counters reset on restart."""
from collections import deque
from contextlib import contextmanager
import hashlib
import hmac
import os
import threading
import time


def hosted():
    return os.getenv('ARCHREVIEW_HOSTED') == '1' or os.getenv('RENDER') == 'true'


def live_authorized(code):
    expected = os.getenv('DEMO_CODE', '')
    return bool(expected) and hmac.compare_digest(
        hashlib.sha256(expected.encode()).digest(),
        hashlib.sha256((code or '').encode()).digest())


class PreviewLimit(ValueError):
    pass


class PreviewBudget:
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.calls = deque()
        self.total = 0
        self.lock = threading.Lock()
        self.slot = threading.BoundedSemaphore(1)

    @contextmanager
    def request(self, code):
        if not hosted():
            yield
            return
        if not self.slot.acquire(blocking=False):
            raise PreviewLimit('One live request is already running. Try again later.')
        try:
            with self.lock:
                now = self.clock()
                while self.calls and self.calls[0] <= now - 3600:
                    self.calls.popleft()
                if len(self.calls) >= 20 or self.total >= 100:
                    raise PreviewLimit('The public demo live-request budget is exhausted. Use a fixture example.')
                self.calls.append(now)
                self.total += 1
            if not live_authorized(code):
                raise PreviewLimit('Live extraction requires the owner-provided demo code.')
            yield
        finally:
            self.slot.release()


LIVE_BUDGET = PreviewBudget()
