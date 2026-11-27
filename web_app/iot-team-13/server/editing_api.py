"""The addresses an editor page calls: to become the editor in use, to keep the draft up to
date, to save or discard it, and to take over from another editor.

Every request carries the editor's id, which the page was given when its live channel
connected (events_api.py). The rules themselves are in one_editor_at_a_time.py; this file only
turns requests into questions for them, and their answers into JSON.

    POST /api/editing/enter                 a newly opened editor asks to be the one in use
    POST /api/editing/draft-left-behind     ... and chose to resume or discard a draft it found
    POST /api/editing/leave                 an editor page is going away. If it was asking to
                                            take over, that stops the asking
    PUT  /api/editing/draft                 the editor in use changed something
    POST /api/editing/save                  the draft becomes the saved layout
    POST /api/editing/discard               the draft is erased
    POST /api/editing/take-over             ask the editor in use to hand over
    POST /api/editing/take-over/approve     the editor in use hands over
    POST /api/editing/take-over/refuse      the editor in use goes on editing

An editor that asks for something it may not do gets status 409, with a `reason` the page can
act on (the names are in one_editor_at_a_time.py).
"""
from __future__ import annotations

from typing import Any, Callable

from flask import Blueprint, jsonify, request

from .one_editor_at_a_time import LayoutNotAccepted, OneEditorAtATime, Refused


class BadRequest(Exception):
    """The request does not say what it must. The message goes back to the page."""


def create_editing_api(editors: OneEditorAtATime) -> Blueprint:
    editing_api = Blueprint("editing_api", __name__)

    def answer(act: Callable[[str, dict], Any]):
        """Read the request, let `act(editor, request_body)` handle it, and send its result as JSON."""
        try:
            # force=True: a page that is closing sends its last message as plain text.
            body = request.get_json(silent=True, force=True)
            if not isinstance(body, dict) or not isinstance(body.get("editor"), str):
                raise BadRequest('The request must be JSON and say which editor is asking: {"editor": "..."}.')
            result = act(body["editor"], body)
        except BadRequest as bad_request:
            return jsonify({"errors": [str(bad_request)]}), 400
        except LayoutNotAccepted as not_accepted:
            return jsonify({"errors": not_accepted.problems}), 400
        except Refused as refused:
            return jsonify({"errors": [refused.message], "reason": refused.reason}), 409
        return jsonify(result if result is not None else {})

    def keep_changes_of(body: dict) -> bool:
        if not isinstance(body.get("keep_changes"), bool):
            raise BadRequest('Say what happens to the unsaved changes: "keep_changes" must be true or false.')
        return body["keep_changes"]

    def layout_of(body: dict) -> Any:
        if "layout" not in body:
            raise BadRequest('The request must carry the layout as it is now: {"layout": {...}}.')
        return body["layout"]

    @editing_api.post("/api/editing/enter")
    def enter():
        return answer(lambda editor, body: editors.enter(editor))

    @editing_api.post("/api/editing/draft-left-behind")
    def answer_about_the_draft_left_behind():
        return answer(lambda editor, body: editors.answer_about_the_draft_left_behind(editor, keep_changes_of(body)))

    @editing_api.post("/api/editing/leave")
    def leave():
        return answer(lambda editor, body: editors.leave(editor))

    @editing_api.put("/api/editing/draft")
    def update_draft():
        return answer(lambda editor, body: editors.update_draft(editor, layout_of(body)))

    @editing_api.post("/api/editing/save")
    def save():
        return answer(lambda editor, body: editors.save(editor))

    @editing_api.post("/api/editing/discard")
    def discard():
        return answer(lambda editor, body: editors.discard(editor))

    @editing_api.post("/api/editing/take-over")
    def ask_to_take_over():
        return answer(lambda editor, body: editors.ask_to_take_over(editor, keep_changes_of(body)))

    @editing_api.post("/api/editing/take-over/approve")
    def approve_take_over():
        return answer(lambda editor, body: editors.approve_take_over(editor))

    @editing_api.post("/api/editing/take-over/refuse")
    def refuse_take_over():
        return answer(lambda editor, body: editors.refuse_take_over(editor))

    return editing_api
