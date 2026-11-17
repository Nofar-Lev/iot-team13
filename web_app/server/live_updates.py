"""Keeps track of the pages that are listening, and sends them news.

A page that opens the live channel becomes a listener. Each listener has its own waiting line of
news; the code that serves the channel takes news from that line and sends it to the page.

Listeners say what they are. A "device" listener is a page that plays the part of the display,
so "is the display online?" simply means "is at least one device listening?".
"""
from __future__ import annotations

import queue
import threading
from typing import Any

# What a listener may call itself.
DEVICE = "device"
LISTENER_ROLES = ("device", "home", "editor")

# News items a slow page may fall behind by before new ones are dropped for it. A page that
# missed news catches up by itself: it compares revision numbers when it reconnects.
LONGEST_WAITING_LINE = 100

# One piece of news: its name, and the details that go with it.
News = tuple[str, dict[str, Any]]


class Listener:
    """One connected page."""

    def __init__(self, role: str):
        self.role = role
        self._waiting_news: "queue.Queue[News]" = queue.Queue(maxsize=LONGEST_WAITING_LINE)

    def next_news(self, wait_seconds: float) -> News:
        """The next piece of news. Raises queue.Empty if none arrives within wait_seconds."""
        return self._waiting_news.get(timeout=wait_seconds)

    def _hand_over(self, news: News) -> None:
        try:
            self._waiting_news.put_nowait(news)
        except queue.Full:
            pass


class LiveUpdates:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._listeners: list[Listener] = []

    def add_listener(self, role: str) -> Listener:
        listener = Listener(role)
        with self._lock:
            display_was_online = self._display_is_online()
            self._listeners.append(listener)
            if role == DEVICE and not display_was_online:
                self._tell_everyone(("display", {"online": True}), except_for=listener)
        return listener

    def remove_listener(self, listener: Listener) -> None:
        with self._lock:
            if listener not in self._listeners:
                return
            self._listeners.remove(listener)
            if listener.role == DEVICE and not self._display_is_online():
                self._tell_everyone(("display", {"online": False}))

    def announce(self, name: str, details: dict[str, Any]) -> None:
        """Send one piece of news to every connected page."""
        with self._lock:
            self._tell_everyone((name, details))

    def display_is_online(self) -> bool:
        with self._lock:
            return self._display_is_online()

    # The two helpers below expect the caller to hold the lock.

    def _display_is_online(self) -> bool:
        return any(listener.role == DEVICE for listener in self._listeners)

    def _tell_everyone(self, news: News, except_for: "Listener | None" = None) -> None:
        for listener in self._listeners:
            if listener is not except_for:
                listener._hand_over(news)
