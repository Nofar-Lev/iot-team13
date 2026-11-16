"""Who is listening, and who gets told what."""
import queue

import pytest

from server.live_updates import LiveUpdates

NO_WAIT = 0.01


def waiting_news(listener):
    """Every piece of news waiting for a listener, oldest first."""
    news = []
    while True:
        try:
            news.append(listener.next_news(wait_seconds=NO_WAIT))
        except queue.Empty:
            return news


def test_an_announcement_reaches_every_listener():
    live_updates = LiveUpdates()
    home, editor = live_updates.add_listener("home"), live_updates.add_listener("editor")
    live_updates.announce("layout", {"revision": 3})
    assert waiting_news(home) == [("layout", {"revision": 3})]
    assert waiting_news(editor) == [("layout", {"revision": 3})]


def test_a_listener_with_no_news_waits_and_then_gives_up():
    listener = LiveUpdates().add_listener("home")
    with pytest.raises(queue.Empty):
        listener.next_news(wait_seconds=NO_WAIT)


def test_the_display_is_offline_until_a_device_listens():
    live_updates = LiveUpdates()
    assert not live_updates.display_is_online()
    live_updates.add_listener("home")
    assert not live_updates.display_is_online()
    live_updates.add_listener("device")
    assert live_updates.display_is_online()


def test_the_others_are_told_when_the_display_comes_online():
    live_updates = LiveUpdates()
    home = live_updates.add_listener("home")
    device = live_updates.add_listener("device")
    assert waiting_news(home) == [("display", {"online": True})]
    assert waiting_news(device) == []   # the device does not need to be told about itself


def test_everyone_is_told_when_the_last_device_leaves():
    live_updates = LiveUpdates()
    home = live_updates.add_listener("home")
    first_device = live_updates.add_listener("device")
    second_device = live_updates.add_listener("device")
    waiting_news(home)

    live_updates.remove_listener(first_device)
    assert live_updates.display_is_online()
    assert waiting_news(home) == []   # one device is still there

    live_updates.remove_listener(second_device)
    assert not live_updates.display_is_online()
    assert waiting_news(home) == [("display", {"online": False})]


def test_a_removed_listener_hears_nothing_more():
    live_updates = LiveUpdates()
    home = live_updates.add_listener("home")
    live_updates.remove_listener(home)
    live_updates.announce("layout", {"revision": 1})
    assert waiting_news(home) == []


def test_removing_a_listener_twice_is_harmless():
    live_updates = LiveUpdates()
    home = live_updates.add_listener("home")
    device = live_updates.add_listener("device")
    waiting_news(home)
    live_updates.remove_listener(device)
    live_updates.remove_listener(device)
    assert waiting_news(home) == [("display", {"online": False})]


def test_a_page_that_stopped_reading_does_not_block_the_others():
    live_updates = LiveUpdates()
    stuck, healthy = live_updates.add_listener("home"), live_updates.add_listener("home")
    for revision in range(500):
        live_updates.announce("layout", {"revision": revision})
        healthy.next_news(wait_seconds=NO_WAIT)
    assert len(waiting_news(stuck)) < 500   # the stuck page lost news, and nothing broke
