"""The frame of the phone editor, used in a real browser set up as a phone held sideways:
which editor a browser gets, the start screen, the preview with its grid, the arrows, the swipe
and the dots between screens, and the main menu.

What the panel's screens do is tested in test_phone_editor_panel.py.
"""
import pytest

from browser_fixtures import COMMON_PHONE, LARGE_PHONE, PHONES, SMALL_PHONE, finger_swipe, sideways, upright
from phone_editor_helpers import expect, open_phone_editor, preview_point, shown_screen, widgets_on_preview

DESKTOP = {"width": 1366, "height": 768}

# The size of one grid cell in the preview, in page units, on each phone held sideways.
CELL_SIZE_ON = {SMALL_PHONE: 84, COMMON_PHONE: 90, LARGE_PHONE: 97}
SMALLEST_FINGER_TARGET = 44


def name_of(phone: tuple) -> str:
    return f"{phone[1]}x{phone[0]}"


# --- Which editor a browser gets -----------------------------------------------------------------

def test_a_phone_gets_the_phone_editor(open_page):
    editor = open_phone_editor(open_page, tap_open=False)
    expect(editor.locator("body")).to_have_class("phone-editor")


def test_a_desktop_still_gets_the_desktop_editor(open_page):
    editor = open_page("/editor", DESKTOP)
    editor.wait_for_selector("body[data-ready]")
    expect(editor.locator("body")).to_have_class("editor-page")


def test_the_address_can_ask_for_the_phone_editor_on_a_desktop(open_page):
    editor = open_page("/editor?view=phone", DESKTOP)
    editor.wait_for_selector("body[data-ready]")
    expect(editor.locator("body")).to_have_class("phone-editor")


def test_the_edit_button_of_the_home_page_opens_the_phone_editor_on_a_phone(open_page):
    home = open_page("/", upright(COMMON_PHONE), as_phone=True)
    home.wait_for_selector("body[data-ready]")
    home.locator("#edit-button").tap()
    expect(home.locator("#open-editor-button")).to_be_visible()


# --- The start screen ------------------------------------------------------------------------------

def test_the_editor_starts_with_one_button_and_opens_on_a_tap(open_page):
    editor = open_phone_editor(open_page, tap_open=False)
    expect(editor.locator("#start-screen")).to_be_visible()
    expect(editor.locator("#editing-screen")).to_be_hidden()

    editor.locator("#open-editor-button").tap()
    expect(editor.locator("#editing-screen")).to_be_visible()
    expect(editor.locator("#start-screen")).to_be_hidden()
    assert editor.evaluate("document.fullscreenElement !== null")


def test_leaving_full_screen_brings_the_start_screen_back(open_page):
    editor = open_phone_editor(open_page)
    editor.locator("#next-screen-button").tap()          # look at the second screen

    editor.evaluate("document.exitFullscreen()")         # what the phone's Back gesture does
    expect(editor.locator("#start-screen")).to_be_visible()

    editor.locator("#open-editor-button").tap()           # and back in: nothing was lost
    expect(editor.locator("#editing-screen")).to_be_visible()
    expect(shown_screen(editor)).to_have_attribute("data-screen", "1")


def test_a_phone_held_upright_is_asked_to_turn(open_page):
    # The test browser cannot turn its own window, like an iPhone's browser.
    editor = open_phone_editor(open_page, viewport=upright(COMMON_PHONE))
    expect(editor.locator(".turn-message")).to_be_visible()


def test_a_phone_held_sideways_is_not_asked_to_turn(open_page):
    editor = open_phone_editor(open_page)
    expect(editor.locator(".turn-message")).to_be_hidden()


# --- The editing screen -----------------------------------------------------------------------------

@pytest.mark.parametrize("phone", PHONES, ids=name_of)
def test_the_editing_screen_fits_the_phone_and_does_not_scroll(open_page, phone):
    viewport = sideways(phone)
    editor = open_phone_editor(open_page, viewport)

    assert editor.evaluate("document.documentElement.scrollWidth") <= viewport["width"]
    assert editor.evaluate("document.documentElement.scrollHeight") <= viewport["height"]

    preview = editor.locator(".preview .display-frame").bounding_box()
    panel = editor.locator("#panel").bounding_box()
    # The preview is whole, and left of the panel; the panel reaches the right edge.
    assert preview["x"] >= 0 and preview["y"] >= 0
    assert preview["y"] + preview["height"] <= viewport["height"]
    assert preview["x"] + preview["width"] <= panel["x"]
    assert panel["x"] + panel["width"] == pytest.approx(viewport["width"], abs=1)
    assert panel["height"] == pytest.approx(viewport["height"], abs=1)


@pytest.mark.parametrize("phone", PHONES, ids=name_of)
def test_the_preview_is_as_large_as_the_screen_allows(open_page, phone):
    editor = open_phone_editor(open_page, sideways(phone))
    preview = editor.locator(".preview .display-frame").bounding_box()

    assert preview["width"] / 6 == pytest.approx(CELL_SIZE_ON[phone], abs=1)
    assert preview["width"] / preview["height"] == pytest.approx(480 / 320, rel=0.01)


def test_the_preview_shows_the_saved_layout(open_page):
    editor = open_phone_editor(open_page)
    expect(widgets_on_preview(editor)).to_have_count(4)


def test_the_grid_is_always_there_behind_the_widgets(open_page):
    editor = open_phone_editor(open_page)
    grid = editor.locator(".preview .display > .preview-grid")
    expect(grid).to_be_visible()

    # Behind: the grid comes before the widgets' layer inside the display.
    order = editor.evaluate(
        "[...document.querySelector('.preview .display').children].map((child) => child.className)"
    )
    assert order.index("preview-grid") < order.index("display__widgets")
    # One square of the grid is one cell of the display.
    assert grid.evaluate("element => getComputedStyle(element).backgroundSize") == "80px 80px"


# --- Moving between screens --------------------------------------------------------------------------

def test_the_arrows_move_between_screens(open_page):
    editor = open_phone_editor(open_page)
    expect(editor.locator("#previous-screen-button")).to_be_disabled()   # this is the first screen

    editor.locator("#next-screen-button").tap()
    expect(shown_screen(editor)).to_have_attribute("data-screen", "1")
    expect(widgets_on_preview(editor)).to_have_count(5)

    editor.locator("#previous-screen-button").tap()
    expect(shown_screen(editor)).to_have_attribute("data-screen", "0")
    expect(widgets_on_preview(editor)).to_have_count(4)


def test_on_the_last_screen_the_right_arrow_offers_a_new_screen(open_page):
    editor = open_phone_editor(open_page)
    next_button = editor.locator("#next-screen-button")
    expect(next_button).to_have_attribute("data-does", "next-screen")

    next_button.tap()                                                    # now on the last screen
    expect(next_button).to_have_attribute("data-does", "add-screen")
    expect(next_button).to_have_attribute("aria-label", "Add a screen")


def test_a_finger_can_hit_an_arrow_a_little_outside_its_circle(open_page):
    editor = open_phone_editor(open_page)
    circle = editor.locator("#next-screen-button").bounding_box()
    assert circle["width"] == pytest.approx(36, abs=0.5)

    # Four units to the right of the circle's edge: outside what is seen, inside what counts.
    editor.touchscreen.tap(circle["x"] + circle["width"] + 4, circle["y"] + circle["height"] / 2)
    expect(shown_screen(editor)).to_have_attribute("data-screen", "1")


def test_a_swipe_on_the_preview_moves_between_screens(open_page):
    editor = open_phone_editor(open_page)

    finger_swipe(editor, preview_point(editor, 0.7, 0.4), preview_point(editor, 0.3, 0.4))   # to the left
    expect(shown_screen(editor)).to_have_attribute("data-screen", "1")

    finger_swipe(editor, preview_point(editor, 0.3, 0.4), preview_point(editor, 0.7, 0.4))   # to the right
    expect(shown_screen(editor)).to_have_attribute("data-screen", "0")


def test_a_swipe_never_goes_past_the_first_or_the_last_screen(open_page):
    editor = open_phone_editor(open_page)

    finger_swipe(editor, preview_point(editor, 0.3, 0.4), preview_point(editor, 0.7, 0.4))   # back, on the first
    expect(shown_screen(editor)).to_have_attribute("data-screen", "0")

    editor.locator("#next-screen-button").tap()
    finger_swipe(editor, preview_point(editor, 0.7, 0.4), preview_point(editor, 0.3, 0.4))   # on, on the last
    expect(shown_screen(editor)).to_have_attribute("data-screen", "1")
    expect(editor.locator(".screen-dots__dot")).to_have_count(2)                              # and no screen was added


def test_a_short_touch_on_the_preview_does_not_change_the_screen(open_page):
    editor = open_phone_editor(open_page)
    finger_swipe(editor, preview_point(editor, 0.5, 0.4), preview_point(editor, 0.47, 0.4))
    expect(shown_screen(editor)).to_have_attribute("data-screen", "0")


def test_the_dots_say_which_screen_is_showing(open_page):
    editor = open_phone_editor(open_page)
    dots = editor.locator(".screen-dots__dot")
    expect(dots).to_have_count(2)
    expect(dots.nth(0)).to_have_class("screen-dots__dot screen-dots__dot--current")

    editor.locator("#next-screen-button").tap()
    expect(dots.nth(1)).to_have_class("screen-dots__dot screen-dots__dot--current")
    expect(dots.nth(0)).to_have_class("screen-dots__dot")


# --- The panel ----------------------------------------------------------------------------------------

def test_the_panel_shows_the_main_menu(open_page):
    editor = open_phone_editor(open_page)
    panel = editor.locator("#panel")
    expect(panel).to_have_attribute("data-showing", "main-menu")

    expect(panel.locator("#home-button")).to_have_text("Home")
    expect(panel.locator("#add-widget-button")).to_have_text("Add widget")
    expect(panel.locator("#backgrounds-button")).to_have_text("Backgrounds")
    expect(panel.locator("#remove-screen-button")).to_have_text("Remove this screen")
    expect(panel.locator("#discard-button")).to_have_text("Discard")
    expect(panel.locator("#save-button")).to_have_text("Save layout")


def test_with_nothing_changed_there_is_nothing_to_save_or_to_discard(open_page):
    editor = open_phone_editor(open_page)
    expect(editor.locator("#save-button")).to_be_disabled()
    expect(editor.locator("#discard-button")).to_be_disabled()


@pytest.mark.parametrize("phone", PHONES, ids=name_of)
def test_the_main_menu_fits_the_panel_and_its_buttons_fit_a_finger(open_page, phone):
    viewport = sideways(phone)
    editor = open_phone_editor(open_page, viewport)

    for button_id in ["home-button", "add-widget-button", "backgrounds-button", "remove-screen-button",
                      "discard-button", "save-button"]:
        box = editor.locator(f"#{button_id}").bounding_box()
        assert box["height"] >= SMALLEST_FINGER_TARGET, button_id
        assert box["y"] >= 0 and box["y"] + box["height"] <= viewport["height"], button_id
    # The main menu is short enough to need no scrolling.
    assert editor.evaluate("(() => { const b = document.querySelector('.panel__body'); return b.scrollHeight <= b.clientHeight; })()")


def test_home_leaves_the_editor_for_the_home_page(open_page):
    editor = open_phone_editor(open_page)
    editor.locator("#home-button").tap()
    editor.wait_for_url("**/")
    editor.wait_for_selector(".home-page")
