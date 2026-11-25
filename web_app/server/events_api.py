"""The live channel: a page keeps this address open, and the server pushes news down it.

This uses "server-sent events", which browsers support by themselves: the answer to the request
never ends, and each piece of news is a few lines of text followed by an empty line.

The news the server sends:

    hello      once, when the page connects: the layout's revision, when it was saved, and
               whether the display is online. An editor is also given its id here, which it
               sends with everything it asks of the server (editing_api.py)
    layout     a new layout was saved: its revision and when it was saved
    display    the display went online or offline
    heartbeat  nothing happened; sent so that both sides notice a connection that died silently

And to one editor only, about taking over (the rules are in one_editor_at_a_time.py):

    take_over_request    another editor asks this one to hand over: whether it will keep this
                         one's unsaved changes, and how many seconds there are to answer
    take_over_withdrawn  the editor that asked no longer does
    taken_over           another editor is now the one in use: what became of this one's changes
    take_over_refused    the editor in use refused to hand over to this one
    take_over_granted    this editor is now the one in use: the saved layout, and the draft

An editor exists for as long as its live channel is connected. When the channel closes, the
editor is gone, and the rules are told.
"""
from __future__ import annotations

import json
import queue
from typing import Any, Iterator

from flask import Blueprint, Response, jsonify, request

from .layout_store import LayoutStore
from .live_updates import EDITOR, LISTENER_ROLES, LiveUpdates
from .one_editor_at_a_time import OneEditorAtATime

# How long a page should wait before it tries to connect again, in milliseconds.
RECONNECT_AFTER_MILLISECONDS = 1000


def format_news(name: str, details: dict[str, Any]) -> str:
    """One piece of news in the text form that browsers expect."""
    return f"event: {name}\ndata: {json.dumps(details)}\n\n"


def create_events_api(
    store: LayoutStore, live_updates: LiveUpdates, editors: OneEditorAtATime, heartbeat_seconds: float,
) -> Blueprint:
    events_api = Blueprint("events_api", __name__)

    @events_api.get("/api/events")
    def open_live_channel():
        role = request.args.get("role", "")
        if role not in LISTENER_ROLES:
            allowed = ", ".join(LISTENER_ROLES)
            return jsonify({"errors": [f"Say who is listening: add ?role= with one of {allowed}."]}), 400

        def news_stream() -> Iterator[str]:
            # The listener is added here, inside the stream, so that the "finally" below is
            # certain to remove it again when the page goes away.
            listener = live_updates.add_listener(role)
            try:
                saved = store.current()
                hello = {
                    "revision": saved.revision,
                    "saved_at": saved.saved_at,
                    "display_online": live_updates.display_is_online(),
                }
                if role == EDITOR:
                    hello["editor"] = listener.id
                yield f"retry: {RECONNECT_AFTER_MILLISECONDS}\n" + format_news("hello", hello)
                while True:
                    try:
                        name, details = listener.next_news(wait_seconds=heartbeat_seconds)
                    except queue.Empty:
                        name, details = "heartbeat", {}
                    yield format_news(name, details)
            finally:
                live_updates.remove_listener(listener)
                if role == EDITOR:
                    editors.leave(listener.id)

        return Response(
            news_stream(),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    return events_api
