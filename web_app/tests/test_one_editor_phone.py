"""One editor at a time, in the phone editor: a phone and a laptop, or two phones, with the
editor open at once in a real browser, against the real server.

The same rules are tried for the desktop editor in test_one_editor_desktop.py. Here it is what
differs on a phone: a newly opened editor meets its questions on the start screen, usually with
the phone upright; the editor in use meets them over the editing screen, with the phone
sideways; and a finger, not a mouse, answers them.
"""
import pytest

from browser_fixtures import COMMON_PHONE, PHONES, eventually, sideways, upright
from phone_editor_helpers import expect, open_phone_editor, panel, tap_cell, widgets_on_preview

DESKTOP = {"width": 1366, "height": 768}
WIDGETS_IN_THE_SAVED_LAYOUT = 4   # on the first screen of the layout the app starts with
THE_WEATHER = (1, 3.5)            # a widget of that layout, in grid cells


# --- Helpers -----------------------------------------------------------------------------------

def message_of(page, name: str):
    """The dialog, while it shows the message with this name."""
    return page.locator(f'#dialog[data-message="{name}"]')


def answer(page, action: str) -> None:
    page.locator(f'#dialog [data-action="{action}"]').tap()


def open_phone_that_is_asked(open_page, message: str, viewport=None):
    """Open the editor on a phone where it must ask the user something first."""
    phone = open_page("/editor", viewport or upright(COMMON_PHONE), as_phone=True)
    expect(message_of(phone, message)).to_be_visible()
    return phone


def tap_open_the_editor(phone) -> None:
    phone.wait_for_selector("body[data-ready]")
    expect(phone.locator("#dialog")).to_be_hidden()
    # A real phone turns the picture sideways at the tap. The test browser does not turn by
    # itself, so the test turns the phone first.
    phone.set_viewport_size(sideways(COMMON_PHONE))
    phone.locator("#open-editor-button").tap()
    expect(phone.locator("#editing-screen")).to_be_visible()


def add_a_date(phone) -> None:
    """Make one unsaved change on the phone, and come back to the main menu."""
    phone.locator("#add-widget-button").tap()
    phone.locator('.widget-row[data-widget-type="date"]').tap()
    phone.locator("#panel-back-button").tap()
    expect(panel(phone)).to_have_attribute("data-showing", "main-menu")


def phone_with_unsaved_changes(open_page, server):
    phone = open_phone_editor(open_page)
    add_a_date(phone)
    eventually(server.read_draft)
    return phone


def laptop_with_unsaved_changes(open_page, server):
    laptop = open_page("/editor", DESKTOP)
    laptop.wait_for_selector("body[data-ready]")
    laptop.click('.palette-entry[data-widget-type="stock"]')
    eventually(server.read_draft)
    return laptop


def expect_the_dialog_to_fit(page, viewport: dict) -> None:
    box = page.locator("#dialog .dialog").bounding_box()
    assert box["x"] >= 0 and box["x"] + box["width"] <= viewport["width"], box
    assert box["y"] >= 0 and box["y"] + box["height"] <= viewport["height"], box


# --- The draft ---------------------------------------------------------------------------------

def test_a_change_on_the_phone_goes_to_the_servers_draft(open_page, server):
    phone = open_phone_editor(open_page)
    assert server.read_draft() is None

    add_a_date(phone)

    draft = eventually(server.read_draft)
    assert len(draft["screens"][0]["widgets"]) == WIDGETS_IN_THE_SAVED_LAYOUT + 1
    assert server.read_layout()["revision"] == 0


def test_a_widget_carried_to_another_place_reaches_the_draft(open_page, server):
    phone = open_phone_editor(open_page)
    tap_cell(phone, *THE_WEATHER)                                  # select it, then change its city
    phone.locator('[data-setting-key="city"] input').fill("Eilat")
    eventually(lambda: "Eilat" in str(server.read_draft()))


# --- A newly opened phone editor meets its questions on the start screen -----------------------

@pytest.mark.parametrize("phone_size", PHONES)
def test_a_draft_left_behind_is_asked_about_on_the_start_screen_of_an_upright_phone(open_page, server, phone_size):
    phone_with_unsaved_changes(open_page, server).close()

    phone = open_phone_that_is_asked(open_page, "draft-left-behind", upright(phone_size))

    expect(phone.locator("#editing-screen")).to_be_hidden()        # the editor has not been opened yet
    expect_the_dialog_to_fit(phone, upright(phone_size))
    # On a narrow screen the buttons go one under the other, each as wide as the dialog.
    buttons = [button.bounding_box() for button in phone.locator("#dialog .dialog__button").all()]
    assert len(buttons) == 3
    assert buttons[0]["y"] < buttons[1]["y"] < buttons[2]["y"]
    assert len({round(button["x"]) for button in buttons}) == 1
    assert all(button["height"] >= 44 for button in buttons)       # large enough for a finger


def test_resuming_on_the_phone_brings_the_button_and_then_the_draft(open_page, server):
    phone_with_unsaved_changes(open_page, server).close()
    phone = open_phone_that_is_asked(open_page, "draft-left-behind")
    expect(phone.locator("#open-editor-button")).to_be_hidden()    # nothing to open before the answer

    answer(phone, "resume")

    tap_open_the_editor(phone)
    expect(widgets_on_preview(phone)).to_have_count(WIDGETS_IN_THE_SAVED_LAYOUT + 1)
    expect(phone.locator("#save-button")).to_be_enabled()          # the changes are still unsaved


def test_discarding_on_the_phone_opens_the_saved_layout(open_page, server):
    phone_with_unsaved_changes(open_page, server).close()
    phone = open_phone_that_is_asked(open_page, "draft-left-behind")

    answer(phone, "discard")

    tap_open_the_editor(phone)
    expect(widgets_on_preview(phone)).to_have_count(WIDGETS_IN_THE_SAVED_LAYOUT)
    expect(phone.locator("#save-button")).to_be_disabled()
    assert server.read_draft() is None


def test_return_to_home_from_the_start_screen_question(open_page, server):
    phone_with_unsaved_changes(open_page, server).close()
    phone = open_phone_that_is_asked(open_page, "draft-left-behind")

    answer(phone, "return-to-home")

    phone.wait_for_url(server.address + "/")
    assert server.read_draft() is not None                         # the draft is as it was


# --- A phone and a laptop ----------------------------------------------------------------------

def test_the_phone_takes_over_from_the_laptop_and_continues_its_changes(open_page, server):
    laptop = laptop_with_unsaved_changes(open_page, server)
    phone = open_phone_that_is_asked(open_page, "another-editor-has-unsaved-changes")
    expect_the_dialog_to_fit(phone, upright(COMMON_PHONE))

    answer(phone, "take-over-and-continue")

    expect(message_of(phone, "waiting-for-the-other-editor")).to_contain_text("seconds left")
    expect(phone.locator(".dialog__countdown-bar")).to_be_visible()
    expect(message_of(laptop, "asked-to-hand-over")).to_be_visible()
    laptop.click('#dialog [data-action="approve"]')

    expect(message_of(laptop, "taken-over")).to_contain_text("carried over")
    tap_open_the_editor(phone)
    expect(widgets_on_preview(phone)).to_have_count(WIDGETS_IN_THE_SAVED_LAYOUT + 1)

    phone.locator("#save-button").tap()                            # the phone is the one that can save now
    expect(phone.locator(".toast")).to_contain_text("Saved.")
    assert len(server.read_layout()["layout"]["screens"][0]["widgets"]) == WIDGETS_IN_THE_SAVED_LAYOUT + 1


@pytest.mark.parametrize("phone_size", PHONES)
def test_a_phone_in_the_editing_screen_is_asked_to_hand_over_and_can_refuse(open_page, server, phone_size):
    phone = open_phone_editor(open_page, viewport=sideways(phone_size))
    add_a_date(phone)
    eventually(server.read_draft)
    laptop = open_page("/editor", DESKTOP)
    expect(message_of(laptop, "another-editor-has-unsaved-changes")).to_be_visible()

    laptop.click('#dialog [data-action="take-over-and-discard"]')

    # The question comes up over the editing screen, and fits a phone held sideways.
    expect(message_of(phone, "asked-to-hand-over")).to_contain_text("Your unsaved changes will be discarded.")
    expect(phone.locator("#editing-screen")).to_be_visible()
    expect_the_dialog_to_fit(phone, sideways(phone_size))
    expect(phone.locator(".dialog__countdown-text")).to_contain_text("it takes over in")

    answer(phone, "refuse")

    expect(phone.locator("#dialog")).to_be_hidden()
    expect(message_of(laptop, "take-over-refused")).to_be_visible()
    expect(widgets_on_preview(phone)).to_have_count(WIDGETS_IN_THE_SAVED_LAYOUT + 1)
    phone.locator("#save-button").tap()                            # and the phone goes on as the editor
    expect(phone.locator(".toast")).to_contain_text("Saved.")


def test_a_phone_that_approves_is_told_what_became_of_its_changes(open_page, server):
    phone = phone_with_unsaved_changes(open_page, server)
    laptop = open_page("/editor", DESKTOP)
    laptop.click('#dialog [data-action="take-over-and-continue"]')
    expect(message_of(phone, "asked-to-hand-over")).to_contain_text("Nothing is lost.")

    answer(phone, "approve")

    expect(message_of(phone, "taken-over")).to_contain_text("Your unsaved changes were carried over to it.")
    laptop.wait_for_selector("body[data-ready]")
    expect(laptop.locator(".display__widgets > .widget")).to_have_count(WIDGETS_IN_THE_SAVED_LAYOUT + 1)

    answer(phone, "return-to-home")
    phone.wait_for_url(server.address + "/")


def test_while_a_question_is_up_touches_do_not_reach_the_editor_behind_it(open_page, server):
    phone = phone_with_unsaved_changes(open_page, server)
    where_add_widget_is = phone.locator("#add-widget-button").bounding_box()
    laptop = open_page("/editor", DESKTOP)
    laptop.click('#dialog [data-action="take-over-and-discard"]')
    expect(message_of(phone, "asked-to-hand-over")).to_be_visible()

    # A finger that was on its way to the panel and to the preview lands after the question came up.
    phone.touchscreen.tap(where_add_widget_is["x"] + 20, where_add_widget_is["y"] + 10)
    tap_cell(phone, 0.3, 3.5)                                      # the weather, left of the dialog

    expect(message_of(phone, "asked-to-hand-over")).to_be_visible()   # nothing was answered
    answer(phone, "refuse")
    expect(panel(phone)).to_have_attribute("data-showing", "main-menu")   # and nothing behind it reacted
    expect(widgets_on_preview(phone)).to_have_count(WIDGETS_IN_THE_SAVED_LAYOUT + 1)


def test_a_phone_still_on_its_start_screen_is_told_when_it_is_taken_over(open_page, server):
    # The phone is the editor in use from the moment its button shows, tapped or not.
    phone = open_phone_editor(open_page, viewport=upright(COMMON_PHONE), tap_open=False)

    laptop = open_page("/editor", DESKTOP)
    laptop.wait_for_selector("body[data-ready]")                   # nothing unsaved on the phone: at once

    expect(message_of(phone, "taken-over")).to_contain_text("You had no unsaved changes.")
    expect_the_dialog_to_fit(phone, upright(COMMON_PHONE))
    answer(phone, "return-to-home")
    phone.wait_for_url(server.address + "/")


@pytest.mark.take_over_seconds(4)
def test_a_phone_that_does_not_answer_sees_its_timer_run_out(open_page, server):
    phone = phone_with_unsaved_changes(open_page, server)
    laptop = open_page("/editor", DESKTOP)
    laptop.click('#dialog [data-action="take-over-and-continue"]')

    timer = phone.locator(".dialog__countdown")
    expect(timer).to_have_attribute("data-stage", "soon")          # amber at half the time
    expect(timer).to_have_attribute("data-stage", "now")           # maroon for the last quarter
    expect(message_of(phone, "taken-over")).to_be_visible()
    laptop.wait_for_selector("body[data-ready]")


# --- A lost connection -------------------------------------------------------------------------

def test_a_phone_that_loses_the_server_stops_and_a_reload_starts_over(open_page, server):
    phone = phone_with_unsaved_changes(open_page, server)

    server.stop()
    expect(message_of(phone, "connection-lost")).to_be_visible(timeout=10000)
    expect_the_dialog_to_fit(phone, sideways(COMMON_PHONE))
    server.start()

    answer(phone, "reload")

    # A reload is a new editor: back on the start screen, asked about the draft it left.
    expect(message_of(phone, "draft-left-behind")).to_be_visible()
    expect(phone.locator("#editing-screen")).to_be_hidden()
    answer(phone, "resume")
    tap_open_the_editor(phone)
    expect(widgets_on_preview(phone)).to_have_count(WIDGETS_IN_THE_SAVED_LAYOUT + 1)


def test_a_server_that_cannot_be_asked_is_a_lost_connection_on_the_start_screen(open_page, server):
    def prepare(page):
        page.route("**/api/editing/enter", lambda route: route.abort())

    phone = open_page("/editor", upright(COMMON_PHONE), as_phone=True, prepare=prepare)
    expect(message_of(phone, "connection-lost")).to_be_visible()
    expect(phone.locator('#dialog [data-action="reload"]')).to_be_visible()


# --- Two phones --------------------------------------------------------------------------------

def test_a_second_phone_is_told_and_a_third_is_asked_to_try_again(open_page, server):
    first = phone_with_unsaved_changes(open_page, server)
    second = open_phone_that_is_asked(open_page, "another-editor-has-unsaved-changes")
    answer(second, "take-over-and-continue")
    expect(message_of(first, "asked-to-hand-over")).to_be_visible()

    third = open_phone_that_is_asked(open_page, "take-over-in-progress")
    expect(message_of(third, "take-over-in-progress")).to_contain_text("Try again in a moment.")

    answer(second, "return-to-home")                               # the second one gives up
    second.wait_for_url(server.address + "/")
    expect(first.locator("#dialog")).to_be_hidden()                # and the first one's question is gone
