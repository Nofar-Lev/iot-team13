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


def save_as_an_editor(app, layout):
    """Save a layout the way an editor page does: connect, become the editor in use, send the
    layout as the draft, and save. Returns each step's (status, answer), as a dictionary with
    "draft" and "save". The editor leaves afterwards."""
    client = app.test_client()
    channel = Channel(app, "editor")
    editor = channel.next_news()[1]["editor"]
    client.post("/api/editing/enter", json={"editor": editor})
    draft = client.put("/api/editing/draft", json={"editor": editor, "layout": layout})
    save = client.post("/api/editing/save", json={"editor": editor})
    channel.close()
    return {"draft": (draft.status_code, draft.get_json()), "save": (save.status_code, save.get_json())}


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
