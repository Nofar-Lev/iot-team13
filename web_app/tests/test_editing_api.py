"""The addresses an editor page calls, tried the way pages use them: each editor keeps a live
channel open, and asks for things with the id it was given there.

The rules themselves are tried in test_one_editor_at_a_time.py; here it is the way in and out.
"""
import json
from dataclasses import replace

import pytest

from live_channel import Channel
from server.app import create_app

SHORT_HEARTBEAT_SECONDS = 0.05


@pytest.fixture
def app(config):
    return create_app(replace(config, heartbeat_seconds=SHORT_HEARTBEAT_SECONDS))


class EditorPage:
    """Stands in for one open editor page: a live channel, and requests that carry its id."""

    def __init__(self, app):
        self._client = app.test_client()
        self.channel = Channel(app, "editor")
        self.id = self.channel.next_news()[1]["editor"]

    def ask(self, address, method="post", **more):
        """Call one of the editing addresses. Returns (status, answer)."""
        response = getattr(self._client, method)(f"/api/editing/{address}", json={"editor": self.id, **more})
        return response.status_code, response.get_json()

    def next_news(self):
        return self.channel.next_news_that_is_not_a_heartbeat()

    def close(self):
        self.channel.close()


@pytest.fixture
def open_editor(app):
    """Opens editor pages, and closes them all when the test ends."""
    pages = []

    def open_one():
        pages.append(EditorPage(app))
        return pages[-1]

    yield open_one
    for page in pages:
        page.close()


@pytest.fixture
def old_editor_with_unsaved_changes(open_editor, one_clock_layout):
    old = open_editor()
    old.ask("enter")
    old.ask("draft", method="put", layout=one_clock_layout)
    return old


def test_the_first_editor_enters_and_gets_the_saved_layout(open_editor, default_layout):
    assert open_editor().ask("enter") == (200, {
        "situation": "editing",
        "saved": {"revision": 0, "saved_at": None, "layout": default_layout},
        "draft": None,
    })


def test_a_request_must_say_which_editor_is_asking(app):
    client = app.test_client()
    for body in ({}, {"editor": 7}, ["a list"], "just text"):
        response = client.post("/api/editing/enter", json=body)
        assert response.status_code == 400
        assert response.get_json()["errors"]
    assert client.post("/api/editing/enter", data="not JSON at all").status_code == 400


def test_an_editor_with_no_live_channel_is_refused(app):
    response = app.test_client().post("/api/editing/enter", json={"editor": "made-up-id"})
    assert response.status_code == 409
    assert response.get_json()["reason"] == "not_connected"
    assert response.get_json()["errors"]


def test_a_change_goes_into_the_draft_and_not_into_what_the_device_shows(app, open_editor, one_clock_layout, default_layout):
    editor = open_editor()
    editor.ask("enter")
    assert editor.ask("draft", method="put", layout=one_clock_layout) == (200, {"has_unsaved_changes": True})
    assert app.test_client().get("/api/layout").get_json() == {"revision": 0, "saved_at": None, "layout": default_layout}


def test_the_draft_is_kept_in_its_own_file_next_to_the_saved_layout(config, open_editor, one_clock_layout):
    editor = open_editor()
    editor.ask("enter")
    editor.ask("draft", method="put", layout=one_clock_layout)
    assert json.loads(config.draft_layout_path.read_text(encoding="utf-8")) == one_clock_layout
    assert config.draft_layout_path.parent == config.saved_layout_path.parent
    assert not config.saved_layout_path.exists()   # nothing was saved


def test_a_draft_update_must_carry_a_good_layout(open_editor, one_clock_layout):
    editor = open_editor()
    editor.ask("enter")
    status, answer = editor.ask("draft", method="put")
    assert status == 400 and answer["errors"]
    one_clock_layout["version"] = 99
    status, answer = editor.ask("draft", method="put", layout=one_clock_layout)
    assert status == 400 and answer["errors"]


def test_saving_makes_the_draft_what_the_device_shows_and_tells_it(app, open_editor, one_clock_layout):
    device = Channel(app, "device")
    device.next_news()
    editor = open_editor()
    editor.ask("enter")
    editor.ask("draft", method="put", layout=one_clock_layout)

    status, answer = editor.ask("save")

    assert status == 200 and answer["revision"] == 1
    assert device.next_news_that_is_not_a_heartbeat() == ("layout", answer)
    assert app.test_client().get("/api/layout").get_json()["layout"] == one_clock_layout
    assert editor.ask("enter")[1]["draft"] is None
    device.close()


def test_discarding_gives_back_the_saved_layout(open_editor, one_clock_layout, default_layout):
    editor = open_editor()
    editor.ask("enter")
    editor.ask("draft", method="put", layout=one_clock_layout)
    assert editor.ask("discard") == (200, {
        "situation": "editing",
        "saved": {"revision": 0, "saved_at": None, "layout": default_layout},
        "draft": None,
    })


def test_an_editor_that_is_not_the_one_in_use_is_refused_with_the_reason(open_editor, old_editor_with_unsaved_changes, one_clock_layout):
    stranger = open_editor()
    for address, method, more in (("draft", "put", {"layout": one_clock_layout}), ("save", "post", {}), ("discard", "post", {})):
        status, answer = stranger.ask(address, method=method, **more)
        assert (status, answer["reason"]) == (409, "not_the_editor_in_use")


def test_a_draft_left_behind_can_be_resumed(open_editor, old_editor_with_unsaved_changes, one_clock_layout):
    old_editor_with_unsaved_changes.close()
    new = open_editor()
    assert new.ask("enter") == (200, {"situation": "draft_left_behind"})
    status, answer = new.ask("draft-left-behind", keep_changes=True)
    assert (status, answer["situation"], answer["draft"]) == (200, "editing", one_clock_layout)


def test_a_draft_left_behind_can_be_discarded(open_editor, old_editor_with_unsaved_changes):
    old_editor_with_unsaved_changes.close()
    new = open_editor()
    new.ask("enter")
    status, answer = new.ask("draft-left-behind", keep_changes=False)
    assert (status, answer["situation"], answer["draft"]) == (200, "editing", None)


@pytest.mark.parametrize("address", ["draft-left-behind", "take-over"])
def test_a_choice_about_unsaved_changes_must_say_what_happens_to_them(open_editor, old_editor_with_unsaved_changes, address):
    new = open_editor()
    for more in ({}, {"keep_changes": "yes"}):
        status, answer = new.ask(address, **more)
        assert status == 400 and answer["errors"]


def test_a_page_that_says_it_is_leaving_frees_the_editor_at_once(app, open_editor, old_editor_with_unsaved_changes):
    old = old_editor_with_unsaved_changes
    # A page that is closing sends its last message as plain text, not marked as JSON.
    response = app.test_client().post(
        "/api/editing/leave", data=json.dumps({"editor": old.id}), content_type="text/plain;charset=UTF-8")
    assert response.status_code == 200
    # Its live channel is still open here, and it no longer holds the editor all the same.
    assert open_editor().ask("enter") == (200, {"situation": "draft_left_behind"})


def test_taking_over_at_once_from_an_editor_with_nothing_unsaved(open_editor):
    old = open_editor()
    old.ask("enter")
    new = open_editor()
    assert new.ask("enter")[1]["situation"] == "editing"
    assert old.next_news() == ("taken_over", {"changes": "none"})
    assert old.ask("save")[0] == 409


def test_a_take_over_that_is_approved(open_editor, old_editor_with_unsaved_changes, one_clock_layout, config):
    old, new = old_editor_with_unsaved_changes, open_editor()
    assert new.ask("enter") == (200, {"situation": "another_editor_has_unsaved_changes"})

    status, answer = new.ask("take-over", keep_changes=True)
    assert (status, answer["situation"]) == (200, "waiting_for_the_other_editor")
    assert 0 < answer["seconds"] <= config.take_over_seconds
    assert old.next_news() == ("take_over_request", {"keep_changes": True, "seconds": config.take_over_seconds})

    assert old.ask("take-over/approve") == (200, {})

    assert old.next_news() == ("taken_over", {"changes": "carried_over"})
    name, details = new.next_news()
    assert (name, details["situation"], details["draft"]) == ("take_over_granted", "editing", one_clock_layout)
    assert new.ask("save")[0] == 200
    assert old.ask("save")[0] == 409


def test_a_take_over_that_is_refused(open_editor, old_editor_with_unsaved_changes):
    old, new = old_editor_with_unsaved_changes, open_editor()
    new.ask("take-over", keep_changes=False)
    old.next_news()

    assert old.ask("take-over/refuse") == (200, {})

    assert new.next_news() == ("take_over_refused", {})
    assert old.ask("enter")[1]["draft"] is not None   # its changes are untouched
    assert new.ask("save")[0] == 409


def test_a_take_over_that_the_new_editor_gives_up(open_editor, old_editor_with_unsaved_changes):
    old, new = old_editor_with_unsaved_changes, open_editor()
    new.ask("take-over", keep_changes=False)
    old.next_news()

    assert new.ask("take-over/give-up") == (200, {})

    assert old.next_news() == ("take_over_withdrawn", {})
    status, answer = old.ask("take-over/approve")
    assert (status, answer["reason"]) == (409, "no_take_over_to_answer")


def test_a_third_editor_is_told_to_try_again_while_a_take_over_waits(open_editor, old_editor_with_unsaved_changes):
    new, third = open_editor(), open_editor()
    new.ask("take-over", keep_changes=True)
    assert third.ask("enter") == (200, {"situation": "take_over_in_progress"})


def test_with_no_answer_the_real_timer_hands_the_editor_over(config, one_clock_layout):
    # The only test that waits for real time: a tenth of a second stands in for the twenty.
    app = create_app(replace(config, heartbeat_seconds=SHORT_HEARTBEAT_SECONDS, take_over_seconds=0.1))
    old, new = EditorPage(app), EditorPage(app)
    old.ask("enter")
    old.ask("draft", method="put", layout=one_clock_layout)
    new.ask("take-over", keep_changes=False)

    name, details = new.next_news()   # nobody answered

    assert (name, details["situation"], details["draft"]) == ("take_over_granted", "editing", None)
    assert old.next_news() == ("take_over_request", {"keep_changes": False, "seconds": 0.1})
    assert old.next_news() == ("taken_over", {"changes": "discarded"})
    old.close()
    new.close()


def test_when_the_old_editor_closes_while_asked_the_new_one_gets_the_editor(open_editor, old_editor_with_unsaved_changes, one_clock_layout):
    old, new = old_editor_with_unsaved_changes, open_editor()
    new.ask("take-over", keep_changes=True)
    old.close()
    name, details = new.next_news()
    assert (name, details["draft"]) == ("take_over_granted", one_clock_layout)
