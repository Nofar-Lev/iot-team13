"""The home page on a phone: the same page as on a desktop, fitted to a small touch screen.

Opened in a real browser set up as a phone (a touch screen, a phone's label), held upright and
held sideways, at the sizes of a small, a common and a large phone.
"""
import pytest

from browser_fixtures import PHONES, sideways, upright

DESKTOP = {"width": 1366, "height": 768}

# The smallest size a finger hits comfortably, in page units (Apple's guideline; Android's is 48).
SMALLEST_FINGER_TARGET = 44

EVERY_WAY_OF_HOLDING = [upright(phone) for phone in PHONES] + [sideways(phone) for phone in PHONES]


def name_of(viewport: dict) -> str:
    return f"{viewport['width']}x{viewport['height']}"


def open_home(open_page, viewport: dict, as_phone: bool = True):
    home = open_page("/", viewport, as_phone=as_phone)
    home.wait_for_selector("body[data-ready]")
    home.wait_for_selector(".display-card__preview .widget")
    return home


@pytest.mark.parametrize("viewport", EVERY_WAY_OF_HOLDING, ids=name_of)
def test_the_home_page_is_never_wider_than_the_phone(open_page, viewport):
    home = open_home(open_page, viewport)

    page_width = home.evaluate("document.documentElement.scrollWidth")
    assert page_width <= viewport["width"]

    # Every card is whole: none of it is past the screen's edges.
    for card in home.locator(".card").all():
        box = card.bounding_box()
        assert box["x"] >= 0
        assert box["x"] + box["width"] <= viewport["width"]


@pytest.mark.parametrize("viewport", EVERY_WAY_OF_HOLDING, ids=name_of)
def test_the_picture_of_the_display_is_whole_and_uses_the_width(open_page, viewport):
    home = open_home(open_page, viewport)
    picture = home.locator(".display-card__preview .display-frame").bounding_box()

    assert picture["x"] >= 0
    assert picture["x"] + picture["width"] <= viewport["width"]
    # It keeps the display's shape, three wide for every two high.
    assert picture["width"] / picture["height"] == pytest.approx(480 / 320, rel=0.01)
    if viewport["width"] < viewport["height"]:
        # Held upright, the picture takes most of the screen's width.
        assert picture["width"] >= 0.75 * viewport["width"]
    else:
        # Held sideways, the whole picture fits in the screen's height, so it can be seen at once.
        assert picture["height"] <= viewport["height"]


@pytest.mark.parametrize("viewport", EVERY_WAY_OF_HOLDING, ids=name_of)
def test_every_button_is_large_enough_for_a_finger(open_page, viewport):
    home = open_home(open_page, viewport)

    buttons = home.locator(".button, .icon-button").all()
    assert len(buttons) >= 5   # Edit, the two screen arrows, Add reminder, the microphone, Send
    for button in buttons:
        box = button.bounding_box()
        assert box["height"] >= SMALLEST_FINGER_TARGET, button.inner_text() or button.get_attribute("aria-label")


def test_the_cards_are_one_under_another_on_a_phone(open_page):
    home = open_home(open_page, upright(PHONES[0]))
    display_card = home.locator(".display-card").bounding_box()
    reminders_card = home.locator("#reminders-card").bounding_box()

    assert reminders_card["y"] >= display_card["y"] + display_card["height"]


def test_a_tap_on_edit_opens_the_editor(open_page):
    home = open_home(open_page, upright(PHONES[0]))
    home.locator("#edit-button").tap()
    home.wait_for_url("**/editor")


def test_the_home_page_keeps_its_two_columns_on_a_desktop(open_page):
    """The phone's rules must not reach a desktop window."""
    home = open_home(open_page, DESKTOP, as_phone=False)
    display_card = home.locator(".display-card").bounding_box()
    reminders_card = home.locator("#reminders-card").bounding_box()

    # Side by side: the reminders start to the right of the display card, at the same height.
    assert reminders_card["x"] >= display_card["x"] + display_card["width"]
    assert reminders_card["y"] == pytest.approx(display_card["y"], abs=1)
    # And the desktop's buttons keep their desktop size.
    assert home.locator("#display-screens .icon-button").first.bounding_box()["height"] == pytest.approx(34, abs=0.5)
