"""Time, as the server's rules use it: what time it is, and "call this after a while".

The rules get this as an object, so that the tests can hand them a clock that moves only when
the test says so.
"""
from __future__ import annotations

import threading
import time
from typing import Callable

# Calling this stops a timer that has not gone off yet.
CancelTimer = Callable[[], None]


class RealTimers:
    def now(self) -> float:
        """Seconds on a clock that only moves forward. Only differences between two readings mean anything."""
        return time.monotonic()

    def call_after(self, seconds: float, callback: Callable[[], None]) -> CancelTimer:
        timer = threading.Timer(seconds, callback)
        timer.daemon = True   # a waiting timer must not keep a stopping server alive
        timer.start()
        return timer.cancel
