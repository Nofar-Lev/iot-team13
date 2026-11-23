"""The live channel, read the way a browser reads it: one piece of news at a time."""
from dataclasses import replace

import pytest

from live_channel import Channel
from server.app import create_app

# The tests use a very short heartbeat, so that "nothing happened" arrives at once.
SHORT_HEARTBEAT_SECONDS = 0.05


@pytest.fixture
def app(config):
    return create_app(replace(config, heartbeat_seconds=SHORT_HEARTBEAT_SECONDS))


def test_the_channel_is_a_stream_of_events(app):
    channel = Channel(app, "home")
    assert channel.status_code == 200
    assert channel.content_type.startswith("text/event-stream")
    channel.close()


def test_the_first_news_says_what_is_saved_and_whether_the_display_is_online(app):
    channel = Channel(app, "home")
    assert channel.next_news() == ("hello", {"revision": 0, "saved_at": None, "display_online": False})
    channel.close()


def test_a_device_that_connects_sees_the_display_as_online(app):
    channel = Channel(app, "device")
    name, details = channel.next_news()
    assert name == "hello"
    assert details["display_online"] is True
    channel.close()


def test_a_heartbeat_arrives_when_nothing_happens(app):
    channel = Channel(app, "home")
    channel.next_news()
    assert channel.next_news() == ("heartbeat", {})
    channel.close()


def test_a_save_reaches_every_connected_page(app, one_clock_layout):
    device, home = Channel(app, "device"), Channel(app, "home")
    device.next_news()
    home.next_news()

    answer = app.test_client().put("/api/layout", json=one_clock_layout).get_json()

    for channel in (device, home):
        name, details = channel.next_news_that_is_not_a_heartbeat()
        assert name == "layout"
        assert details == {"revision": 1, "saved_at": answer["saved_at"]}
        channel.close()


def test_a_refused_save_is_not_announced(app, one_clock_layout):
    device = Channel(app, "device")
    device.next_news()
    one_clock_layout["version"] = 99
    app.test_client().put("/api/layout", json=one_clock_layout)
    assert device.next_news() == ("heartbeat", {})
    device.close()


def test_the_home_page_hears_the_display_come_and_go(app):
    home = Channel(app, "home")
    home.next_news()

    device = Channel(app, "device")
    device.next_news()
    assert home.next_news_that_is_not_a_heartbeat() == ("display", {"online": True})

    device.close()
    assert home.next_news_that_is_not_a_heartbeat() == ("display", {"online": False})
    home.close()


def test_a_page_that_reconnects_learns_the_newest_revision(app, one_clock_layout):
    app.test_client().put("/api/layout", json=one_clock_layout)
    app.test_client().put("/api/layout", json=one_clock_layout)
    channel = Channel(app, "device")
    name, details = channel.next_news()
    assert (name, details["revision"]) == ("hello", 2)
    channel.close()


@pytest.mark.parametrize("address", ["/api/events", "/api/events?role=stranger"])
def test_a_listener_must_say_what_it_is(app, address):
    response = app.test_client().get(address)
    assert response.status_code == 400
    assert response.get_json()["errors"]


def test_an_editor_is_given_an_id_of_its_own(app):
    first, second = Channel(app, "editor"), Channel(app, "editor")
    first_id, second_id = first.next_news()[1]["editor"], second.next_news()[1]["editor"]
    assert first_id and second_id and first_id != second_id
    first.close()
    second.close()


def test_an_editor_that_closes_its_channel_is_no_longer_the_editor_in_use(app, one_clock_layout):
    client = app.test_client()
    first = Channel(app, "editor")
    first_id = first.next_news()[1]["editor"]
    client.post("/api/editing/enter", json={"editor": first_id})
    client.put("/api/editing/draft", json={"editor": first_id, "layout": one_clock_layout})

    first.close()

    second = Channel(app, "editor")
    second_id = second.next_news()[1]["editor"]
    answer = client.post("/api/editing/enter", json={"editor": second_id}).get_json()
    assert answer == {"situation": "draft_left_behind"}   # the draft stayed, and nobody holds the editor
    assert client.post("/api/editing/save", json={"editor": first_id}).status_code == 409
    second.close()
