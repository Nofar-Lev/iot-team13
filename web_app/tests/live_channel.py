"""What the tests of the live channel share: reading news the way a page does."""
import json
import queue

NO_WAIT = 0.01


def waiting_news(listener):
    """Every piece of news waiting for a listener of LiveUpdates, oldest first."""
    news = []
    while True:
        try:
            news.append(listener.next_news(wait_seconds=NO_WAIT))
        except queue.Empty:
            return news


class Channel:
    """One open live channel of the running app, read one piece of news at a time."""

    def __init__(self, app, role):
        self._response = app.test_client().get(f"/api/events?role={role}", buffered=False)
        self._pieces = self._response.iter_encoded()
        self.status_code = self._response.status_code
        self.content_type = self._response.content_type

    def next_news(self):
        """The next piece of news as (name, details)."""
        lines = next(self._pieces).decode("utf-8").splitlines()
        name = next(line for line in lines if line.startswith("event: "))[len("event: "):]
        details = next(line for line in lines if line.startswith("data: "))[len("data: "):]
        return name, json.loads(details)

    def next_news_that_is_not_a_heartbeat(self):
        while True:
            name, details = self.next_news()
            if name != "heartbeat":
                return name, details

    def close(self):
        self._response.close()
