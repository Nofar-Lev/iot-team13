"""Which editor page the server sends: the desktop editor or the phone editor."""
import pytest

from server.which_editor import DESKTOP_EDITOR_PAGE, PHONE_EDITOR_PAGE, editor_page_for, is_a_phone

# The labels that real browsers send.
ANDROID_PHONE = ("Mozilla/5.0 (Linux; Android 14; SM-S911B) AppleWebKit/537.36 (KHTML, like Gecko) "
                 "Chrome/130.0.0.0 Mobile Safari/537.36")
SAMSUNG_BROWSER_ON_A_PHONE = ("Mozilla/5.0 (Linux; Android 14; SAMSUNG SM-S911B) AppleWebKit/537.36 (KHTML, like Gecko) "
                              "SamsungBrowser/25.0 Chrome/121.0.0.0 Mobile Safari/537.36")
IPHONE = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) "
          "Version/17.5 Mobile/15E148 Safari/604.1")
WINDOWS_DESKTOP = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/130.0.0.0 Safari/537.36")
ANDROID_TABLET = ("Mozilla/5.0 (Linux; Android 14; SM-X710) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/130.0.0.0 Safari/537.36")
IPAD = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/17.5 Safari/605.1.15")


@pytest.mark.parametrize("label", [ANDROID_PHONE, SAMSUNG_BROWSER_ON_A_PHONE, IPHONE])
def test_a_phone_is_recognised_by_its_label(label):
    assert is_a_phone(label)
    assert editor_page_for(label) == PHONE_EDITOR_PAGE


@pytest.mark.parametrize("label", [WINDOWS_DESKTOP, ANDROID_TABLET, IPAD, "", None])
def test_a_desktop_a_tablet_and_a_browser_without_a_label_get_the_desktop_editor(label):
    assert not is_a_phone(label)
    assert editor_page_for(label) == DESKTOP_EDITOR_PAGE


def test_the_choice_by_hand_wins_over_the_label():
    assert editor_page_for(WINDOWS_DESKTOP, "phone") == PHONE_EDITOR_PAGE
    assert editor_page_for(ANDROID_PHONE, "desktop") == DESKTOP_EDITOR_PAGE


@pytest.mark.parametrize("not_a_view", ["", "tablet", "PHONE", "editor_phone.html", "../data/default_layout.json"])
def test_an_unknown_choice_is_ignored(not_a_view):
    assert editor_page_for(WINDOWS_DESKTOP, not_a_view) == DESKTOP_EDITOR_PAGE
    assert editor_page_for(ANDROID_PHONE, not_a_view) == PHONE_EDITOR_PAGE


# --- As the server hands the pages out -----------------------------------------------------------

def editor_as_sent(client, address="/editor", label=None):
    headers = {"User-Agent": label} if label is not None else {}
    return client.get(address, headers=headers)


def test_a_desktop_browser_is_sent_the_desktop_editor(client):
    page = editor_as_sent(client, label=WINDOWS_DESKTOP).get_data(as_text=True)
    assert 'src="static/js/editor/editor_main.js"' in page
    assert "editor_phone" not in page


def test_a_phone_is_sent_the_phone_editor(client):
    page = editor_as_sent(client, label=ANDROID_PHONE).get_data(as_text=True)
    assert 'src="static/js/editor_phone/phone_editor_main.js"' in page


def test_the_address_can_ask_for_either_editor(client):
    assert "editor_phone" in editor_as_sent(client, "/editor?view=phone", WINDOWS_DESKTOP).get_data(as_text=True)
    assert "editor_phone" not in editor_as_sent(client, "/editor?view=desktop", ANDROID_PHONE).get_data(as_text=True)


def test_browsers_are_told_that_the_editor_depends_on_their_label(client):
    response = editor_as_sent(client, label=ANDROID_PHONE)
    assert response.headers["Vary"] == "User-Agent"
    assert response.headers["Cache-Control"] == "no-cache"
