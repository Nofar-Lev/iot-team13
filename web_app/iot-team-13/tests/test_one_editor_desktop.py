"""One editor at a time, in the desktop editor: several editors open at once in a real browser,
against the real server.

The rules themselves are tried without a browser (test_one_editor_at_a_time.py), and the
editor page's part in them without a server (js_tests/editing_session.test.js). Here it is the
whole thing, the way people meet it: what each editor shows, and what its buttons do.

Each editor is opened in a browser window of its own, like two people on two computers.
"""
import pytest

from browser_fixtures import eventually

playwright_api = pytest.importorskip("playwright.sync_api")
expect = playwright_api.expect

DESKTOP = {"width": 1366, "height": 768}
PHONE_HELD_SIDEWAYS = {"width": 800, "height": 360}

WIDGETS_IN_THE_SAVED_LAYOUT = 4   # on the first screen of the layout the app starts with


# --- Helpers -----------------------------------------------------------------------------------

def open_editor(open_page):
    """Open the editor where nothing stands in its way: it becomes the editor in use."""
    editor = open_page("/editor", DESKTOP)
    editor.wait_for_selector("body[data-ready]")
    return editor


def open_editor_that_is_asked(open_page, message: str):
    """Open the editor where it must ask the user something first."""
    editor = open_page("/editor", DESKTOP)
    expect(message_of(editor, message)).to_be_visible()
    return editor


def message_of(page, name: str):
    """The dialog, while it shows the message with this name."""
    return page.locator(f'#dialog[data-message="{name}"]')


def answer(page, action: str) -> None:
    page.click(f'#dialog [data-action="{action}"]')


def no_dialog(page):
    return expect(page.locator("#dialog")).to_be_hidden()


def widgets_on_display(page):
    return page.locator(".display__widgets > .widget")


def add_a_widget(editor) -> None:
    """Make one unsaved change, and wait until it has reached the server's draft."""
    before = widgets_on_display(editor).count()
    editor.click('.palette-entry[data-widget-type="stock"]')
    expect(widgets_on_display(editor)).to_have_count(before + 1)


def editor_with_unsaved_changes(open_page, server):
    editor = open_editor(open_page)
    add_a_widget(editor)
    eventually(server.read_draft)
    return editor


def widgets_in(layout: dict) -> int:
    return len(layout["screens"][0]["widgets"])


# --- The draft ---------------------------------------------------------------------------------

def test_a_change_goes_to_the_servers_draft_and_not_to_the_device(open_page, server):
    device = open_page("/device", PHONE_HELD_SIDEWAYS)
    editor = open_editor(open_page)
    assert server.read_draft() is None

    add_a_widget(editor)

    draft = eventually(server.read_draft)
    assert widgets_in(draft) == WIDGETS_IN_THE_SAVED_LAYOUT + 1
    assert widgets_in(server.read_layout()["layout"]) == WIDGETS_IN_THE_SAVED_LAYOUT
    expect(widgets_on_display(device)).to_have_count(WIDGETS_IN_THE_SAVED_LAYOUT)


def test_saving_makes_the_draft_the_saved_layout_and_erases_it(open_page, server):
    editor = editor_with_unsaved_changes(open_page, server)
    editor.click("#save-button")
    expect(editor.locator(".toast")).to_contain_text("Saved")
    expect(editor.locator("#unsaved-mark")).to_be_hidden()
    assert server.read_draft() is None
    assert widgets_in(server.read_layout()["layout"]) == WIDGETS_IN_THE_SAVED_LAYOUT + 1


def test_discarding_erases_the_draft_on_the_server(open_page, server):
    editor = editor_with_unsaved_changes(open_page, server)
    editor.click("#discard-button")
    editor.click("#discard-button")   # the second click confirms
    expect(widgets_on_display(editor)).to_have_count(WIDGETS_IN_THE_SAVED_LAYOUT)
    expect(editor.locator("#unsaved-mark")).to_be_hidden()
    eventually(lambda: server.read_draft() is None)
    assert server.read_layout()["revision"] == 0


def test_undoing_a_change_by_hand_leaves_nothing_unsaved_on_the_server(open_page, server):
    editor = editor_with_unsaved_changes(open_page, server)
    editor.keyboard.press("Delete")   # the widget that was just added is the selected one
    expect(editor.locator("#unsaved-mark")).to_be_hidden()
    eventually(lambda: server.read_draft() is None)


# --- A draft that was left behind --------------------------------------------------------------

def test_a_closed_editor_leaves_its_draft_and_the_next_one_can_resume_it(open_page, server):
    editor_with_unsaved_changes(open_page, server).close()

    editor = open_editor_that_is_asked(open_page, "draft-left-behind")
    # Behind the question, the display shows what is saved.
    expect(widgets_on_display(editor)).to_have_count(WIDGETS_IN_THE_SAVED_LAYOUT)

    answer(editor, "resume")
    editor.wait_for_selector("body[data-ready]")
    no_dialog(editor)
    expect(widgets_on_display(editor)).to_have_count(WIDGETS_IN_THE_SAVED_LAYOUT + 1)
    expect(editor.locator("#unsaved-mark")).to_be_visible()
    expect(editor.locator("#save-button")).to_be_enabled()


def test_a_draft_that_was_left_behind_can_be_discarded(open_page, server):
    editor_with_unsaved_changes(open_page, server).close()
    editor = open_editor_that_is_asked(open_page, "draft-left-behind")

    answer(editor, "discard")

    editor.wait_for_selector("body[data-ready]")
    expect(widgets_on_display(editor)).to_have_count(WIDGETS_IN_THE_SAVED_LAYOUT)
    expect(editor.locator("#unsaved-mark")).to_be_hidden()
    assert server.read_draft() is None


def test_returning_home_from_the_question_leaves_the_draft_as_it_is(open_page, server):
    editor_with_unsaved_changes(open_page, server).close()
    editor = open_editor_that_is_asked(open_page, "draft-left-behind")

    answer(editor, "return-to-home")

    editor.wait_for_url(server.address + "/")
    assert widgets_in(server.read_draft()) == WIDGETS_IN_THE_SAVED_LAYOUT + 1
    open_editor_that_is_asked(open_page, "draft-left-behind")   # and the next editor is asked again


def test_a_reloaded_editor_is_a_new_one_and_is_asked_about_its_own_draft(open_page, server):
    editor = editor_with_unsaved_changes(open_page, server)
    editor.reload()
    # Not "another editor has unsaved changes": the page said it was leaving, so the server
    # does not take the page that is gone for an editor that is still there.
    expect(message_of(editor, "draft-left-behind")).to_be_visible()


def test_a_draft_survives_a_restart_of_the_server(open_page, server):
    editor_with_unsaved_changes(open_page, server).close()
    server.stop()
    server.start()
    editor = open_editor_that_is_asked(open_page, "draft-left-behind")
    answer(editor, "resume")
    expect(widgets_on_display(editor)).to_have_count(WIDGETS_IN_THE_SAVED_LAYOUT + 1)


# --- Another editor is in use, with nothing unsaved --------------------------------------------

def test_a_new_editor_takes_over_at_once_from_one_with_nothing_unsaved(open_page, server):
    old = open_editor(open_page)
    new = open_editor(open_page)   # it opens with nothing to ask

    no_dialog(new)
    expect(message_of(old, "taken-over")).to_contain_text("You had no unsaved changes.")
    add_a_widget(new)
    eventually(server.read_draft)

    answer(old, "return-to-home")
    old.wait_for_url(server.address + "/")
    no_dialog(new)   # the old editor leaving does not disturb the new one


# --- Another editor is in use, with unsaved changes --------------------------------------------

def test_a_new_editor_is_told_of_unsaved_changes_and_the_old_one_is_left_alone(open_page, server):
    old = editor_with_unsaved_changes(open_page, server)
    new = open_editor_that_is_asked(open_page, "another-editor-has-unsaved-changes")

    no_dialog(old)
    answer(new, "return-to-home")
    new.wait_for_url(server.address + "/")
    no_dialog(old)
    add_a_widget(old)   # the old editor goes on editing
    eventually(lambda: widgets_in(server.read_draft()) == WIDGETS_IN_THE_SAVED_LAYOUT + 2)


def test_take_over_and_continue_approved(open_page, server):
    old = editor_with_unsaved_changes(open_page, server)
    new = open_editor_that_is_asked(open_page, "another-editor-has-unsaved-changes")

    answer(new, "take-over-and-continue")

    expect(message_of(new, "waiting-for-the-other-editor")).to_contain_text("seconds left")
    expect(message_of(old, "asked-to-hand-over")).to_contain_text("It will continue from your unsaved changes.")
    expect(message_of(old, "asked-to-hand-over")).to_contain_text("If you do not answer, it takes over in")
    # Approving loses nothing here, so the button is the ordinary one.
    expect(old.locator('#dialog [data-action="approve"]')).to_have_class("dialog__button dialog__button--main")

    answer(old, "approve")

    expect(message_of(old, "taken-over")).to_contain_text("Your unsaved changes were carried over to it.")
    new.wait_for_selector("body[data-ready]")
    no_dialog(new)
    expect(widgets_on_display(new)).to_have_count(WIDGETS_IN_THE_SAVED_LAYOUT + 1)
    expect(new.locator("#unsaved-mark")).to_be_visible()

    new.click("#save-button")   # the new editor is the one that can save now
    expect(new.locator(".toast")).to_contain_text("Saved")
    assert widgets_in(server.read_layout()["layout"]) == WIDGETS_IN_THE_SAVED_LAYOUT + 1


def test_take_over_and_discard_approved(open_page, server):
    old = editor_with_unsaved_changes(open_page, server)
    new = open_editor_that_is_asked(open_page, "another-editor-has-unsaved-changes")

    answer(new, "take-over-and-discard")

    expect(message_of(old, "asked-to-hand-over")).to_contain_text("Your unsaved changes will be discarded.")
    # Approving throws work away here, and the button says so with its colour.
    expect(old.locator('#dialog [data-action="approve"]')).to_have_class("dialog__button dialog__button--discards")

    answer(old, "approve")

    expect(message_of(old, "taken-over")).to_contain_text("Your unsaved changes were discarded.")
    new.wait_for_selector("body[data-ready]")
    expect(widgets_on_display(new)).to_have_count(WIDGETS_IN_THE_SAVED_LAYOUT)
    expect(new.locator("#unsaved-mark")).to_be_hidden()
    assert server.read_draft() is None


def test_a_refused_take_over_leaves_the_old_editor_editing(open_page, server):
    old = editor_with_unsaved_changes(open_page, server)
    new = open_editor_that_is_asked(open_page, "another-editor-has-unsaved-changes")
    answer(new, "take-over-and-discard")
    expect(message_of(old, "asked-to-hand-over")).to_be_visible()

    answer(old, "refuse")

    expect(message_of(new, "take-over-refused")).to_contain_text("It chose to go on editing.")
    no_dialog(old)
    expect(widgets_on_display(old)).to_have_count(WIDGETS_IN_THE_SAVED_LAYOUT + 1)
    old.click("#save-button")
    expect(old.locator(".toast")).to_contain_text("Saved")

    answer(new, "return-to-home")
    new.wait_for_url(server.address + "/")


def test_when_the_new_editor_goes_home_while_waiting_the_question_disappears(open_page, server):
    old = editor_with_unsaved_changes(open_page, server)
    new = open_editor_that_is_asked(open_page, "another-editor-has-unsaved-changes")
    answer(new, "take-over-and-continue")
    expect(message_of(old, "asked-to-hand-over")).to_be_visible()

    answer(new, "return-to-home")

    new.wait_for_url(server.address + "/")
    no_dialog(old)
    add_a_widget(old)
    eventually(lambda: widgets_in(server.read_draft()) == WIDGETS_IN_THE_SAVED_LAYOUT + 2)


def test_a_third_editor_is_told_to_try_again_while_a_take_over_waits(open_page, server):
    old = editor_with_unsaved_changes(open_page, server)
    new = open_editor_that_is_asked(open_page, "another-editor-has-unsaved-changes")
    answer(new, "take-over-and-continue")
    expect(message_of(old, "asked-to-hand-over")).to_be_visible()

    third = open_editor_that_is_asked(open_page, "take-over-in-progress")

    expect(message_of(third, "take-over-in-progress")).to_contain_text("Try again in a moment.")
    expect(message_of(old, "asked-to-hand-over")).to_be_visible()   # the two are not disturbed
    expect(message_of(new, "waiting-for-the-other-editor")).to_be_visible()
    answer(third, "return-to-home")
    third.wait_for_url(server.address + "/")


@pytest.mark.take_over_seconds(4)
def test_with_no_answer_the_timer_runs_out_and_the_new_editor_takes_over(open_page, server):
    old = editor_with_unsaved_changes(open_page, server)
    new = open_editor_that_is_asked(open_page, "another-editor-has-unsaved-changes")

    answer(new, "take-over-and-continue")

    # The old editor's timer warns as it runs out: calm, then amber, then maroon. The new
    # editor's timer stays calm: for it, the time running out is good news.
    old_timer, new_timer = old.locator(".dialog__countdown"), new.locator(".dialog__countdown")
    expect(old_timer).to_have_attribute("data-stage", "calm")
    expect(old_timer).to_have_attribute("data-stage", "soon")
    expect(new_timer).to_have_attribute("data-stage", "calm")
    expect(old_timer).to_have_attribute("data-stage", "now")
    expect(new_timer).to_have_attribute("data-stage", "calm")

    # Nobody answers.
    expect(message_of(old, "taken-over")).to_contain_text("Your unsaved changes were carried over to it.")
    new.wait_for_selector("body[data-ready]")
    expect(widgets_on_display(new)).to_have_count(WIDGETS_IN_THE_SAVED_LAYOUT + 1)


def test_keys_typed_while_asked_do_not_reach_the_editor_or_press_a_button(open_page, server):
    old = editor_with_unsaved_changes(open_page, server)   # the widget it added is selected
    new = open_editor_that_is_asked(open_page, "another-editor-has-unsaved-changes")
    answer(new, "take-over-and-discard")
    expect(message_of(old, "asked-to-hand-over")).to_be_visible()

    # The user was in the middle of something when the question appeared.
    for key in ("Delete", "Enter", " ", "ArrowRight", "Control+s"):
        old.keyboard.press(key)

    expect(message_of(old, "asked-to-hand-over")).to_be_visible()      # nothing was answered
    expect(message_of(new, "waiting-for-the-other-editor")).to_be_visible()
    assert server.read_layout()["revision"] == 0                       # nothing was saved
    answer(old, "refuse")
    expect(widgets_on_display(old)).to_have_count(WIDGETS_IN_THE_SAVED_LAYOUT + 1)   # nothing was removed


# --- A lost connection -------------------------------------------------------------------------

def test_an_editor_that_loses_the_server_stops_and_a_reload_resumes_the_draft(open_page, server):
    editor = editor_with_unsaved_changes(open_page, server)

    server.stop()
    expect(message_of(editor, "connection-lost")).to_be_visible(timeout=10000)
    expect(editor.locator('#dialog [data-action="reload"]')).to_be_visible()

    server.start()
    # The editor does not come back by itself: someone else may have opened it meanwhile.
    editor.wait_for_timeout(1500)
    expect(message_of(editor, "connection-lost")).to_be_visible()

    answer(editor, "reload")
    expect(message_of(editor, "draft-left-behind")).to_be_visible()
    answer(editor, "resume")
    expect(widgets_on_display(editor)).to_have_count(WIDGETS_IN_THE_SAVED_LAYOUT + 1)


def test_after_a_lost_connection_a_reload_meets_whoever_opened_the_editor_meanwhile(open_page, server):
    first = editor_with_unsaved_changes(open_page, server)
    server.stop()
    expect(message_of(first, "connection-lost")).to_be_visible(timeout=10000)
    server.start()

    second = open_editor_that_is_asked(open_page, "draft-left-behind")
    answer(second, "resume")
    second.wait_for_selector("body[data-ready]")

    answer(first, "reload")
    # The first editor is the new one now, and the second is the one in use.
    expect(message_of(first, "another-editor-has-unsaved-changes")).to_be_visible()
    no_dialog(second)


# --- Leaving through the Home link -------------------------------------------------------------

def test_home_with_nothing_unsaved_simply_leaves(open_page, server):
    editor = open_editor(open_page)
    editor.click("#home-link")
    editor.wait_for_url(server.address + "/")


def test_home_with_unsaved_changes_asks_what_should_happen_to_them(open_page, server):
    editor = editor_with_unsaved_changes(open_page, server)
    editor.click("#home-link")

    question = message_of(editor, "leaving-with-unsaved-changes")
    expect(question).to_contain_text("You have unsaved changes")
    expect(question.locator(".dialog__button-label")).to_have_text(["Keep as draft", "Save changes", "Discard changes"])
    expect(question.locator(".dialog__button-explanation")).to_have_text([
        "Finish later. The display stays as it is.",
        "The display shows them now.",
        "Your changes are erased.",
    ])
    expect(question.locator(".dialog__dismiss-line")).to_have_text("Return to the editor")


def test_keep_as_draft_leaves_and_the_changes_wait_on_the_server(open_page, server):
    editor = editor_with_unsaved_changes(open_page, server)
    editor.click("#home-link")
    answer(editor, "keep-as-draft")

    editor.wait_for_url(server.address + "/")
    assert widgets_in(server.read_draft()) == WIDGETS_IN_THE_SAVED_LAYOUT + 1
    assert server.read_layout()["revision"] == 0
    # The editor was told that it left, so the next one is not held up by it.
    open_editor_that_is_asked(open_page, "draft-left-behind")


def test_save_changes_saves_and_leaves(open_page, server):
    editor = editor_with_unsaved_changes(open_page, server)
    editor.click("#home-link")
    answer(editor, "save-changes")

    editor.wait_for_url(server.address + "/")
    assert server.read_draft() is None
    assert widgets_in(server.read_layout()["layout"]) == WIDGETS_IN_THE_SAVED_LAYOUT + 1


def test_discard_changes_discards_and_leaves(open_page, server):
    editor = editor_with_unsaved_changes(open_page, server)
    editor.click("#home-link")
    answer(editor, "discard-changes")

    editor.wait_for_url(server.address + "/")
    assert server.read_draft() is None
    assert server.read_layout()["revision"] == 0


def stay_by_the_line(editor):
    answer(editor, "dismiss")


def stay_by_the_x(editor):
    answer(editor, "dismiss-with-x")


def stay_by_a_click_beside_the_dialog(editor):
    editor.mouse.click(40, 400)


def stay_by_the_escape_key(editor):
    editor.keyboard.press("Escape")


@pytest.mark.parametrize("stay", [
    stay_by_the_line, stay_by_the_x, stay_by_a_click_beside_the_dialog, stay_by_the_escape_key,
])
def test_every_quiet_way_out_of_the_question_returns_to_the_editor(open_page, server, stay):
    editor = editor_with_unsaved_changes(open_page, server)
    editor.click("#home-link")
    expect(message_of(editor, "leaving-with-unsaved-changes")).to_be_visible()

    stay(editor)

    no_dialog(editor)
    assert editor.url == server.address + "/editor"
    expect(widgets_on_display(editor)).to_have_count(WIDGETS_IN_THE_SAVED_LAYOUT + 1)
    expect(editor.locator("#unsaved-mark")).to_be_visible()
    add_a_widget(editor)   # and the editor can be used again
    eventually(lambda: widgets_in(server.read_draft()) == WIDGETS_IN_THE_SAVED_LAYOUT + 2)


def test_closing_the_tab_asks_nothing(open_page, server):
    editor = editor_with_unsaved_changes(open_page, server)
    asked = []
    editor.on("dialog", lambda browser_question: (asked.append(browser_question.message), browser_question.accept()))
    # Closed the way a person closes a tab: the page gets its chance to ask, and does not take it.
    with editor.expect_event("close"):
        editor.close(run_before_unload=True)
    assert asked == []
    assert widgets_in(server.read_draft()) == WIDGETS_IN_THE_SAVED_LAYOUT + 1
