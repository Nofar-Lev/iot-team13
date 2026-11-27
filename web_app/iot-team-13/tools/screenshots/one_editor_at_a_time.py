"""The screenshots of Documentation/web_app_design_decisions/one_editor_at_a_time.md: what the
editors show when the editor is open in two places at once.

The scenes follow one another like a short play with a laptop and a phone, because each
picture needs the situation the one before it left behind. The take-over timer is the real
one, 20 seconds, so that the pictures show the real numbers; the set takes about a minute and
a half.
"""
from __future__ import annotations

import time

PICTURES_FOLDER = "Documentation/web_app_design_decisions/screenshots"

# How long to wait for a message that only comes when the take-over timer has run out.
LONGER_THAN_THE_TAKE_OVER_TIMER_MS = 30_000

# A pause that lets a change reach the server's draft, or a closed page be noticed.
A_MOMENT_MS = 600


# ---- What the scenes do with a page ----------------------------------------------------------

def wait_for_message(page, name: str, timeout_ms: int = 10_000) -> None:
    page.wait_for_selector(f'#dialog[data-message="{name}"]', timeout=timeout_ms)


def wait_for_timer_stage(page, stage: str) -> None:
    """Wait until the timer bar has the colour of this stage: "soon" (amber) or "now" (maroon)."""
    page.wait_for_selector(f'.dialog__countdown[data-stage="{stage}"]', timeout=LONGER_THAN_THE_TAKE_OVER_TIMER_MS)
    page.wait_for_timeout(1200)   # a little into the stage, where the colour has settled


def click_answer(page, action: str) -> None:
    page.click(f'#dialog [data-action="{action}"]')


def tap_answer(page, action: str) -> None:
    page.locator(f'#dialog [data-action="{action}"]').tap()


def wait_until_it_is_the_editor(page) -> None:
    page.wait_for_selector("body[data-ready]")


def change_something_on_the_laptop(laptop) -> None:
    laptop.click('.palette-entry[data-widget-type="stock"]')
    laptop.wait_for_timeout(A_MOMENT_MS)


def open_the_editing_screen_and_change_something(phone) -> None:
    phone.locator("#open-editor-button").tap()
    phone.wait_for_timeout(A_MOMENT_MS)
    phone.locator("#add-widget-button").tap()
    phone.locator('.widget-row[data-widget-type="date"]').tap()
    phone.locator("#panel-back-button").tap()
    phone.wait_for_timeout(A_MOMENT_MS)


def close_the_tab(*pages) -> None:
    """Close pages the way a tab is closed, and give the server a moment to hear of it: a
    closing page tells the server that it is leaving."""
    for page in pages:
        page.close()
    time.sleep(A_MOMENT_MS / 1000)


# ---- The scenes ------------------------------------------------------------------------------

def a_laptop_asks_before_leaving(studio):
    """A laptop has unsaved changes, and its Home link asks what should happen to them."""
    laptop = studio.laptop("/editor")
    wait_until_it_is_the_editor(laptop)
    change_something_on_the_laptop(laptop)

    laptop.click("#home-link")
    wait_for_message(laptop, "leaving-with-unsaved-changes")
    studio.shot(laptop, "desktop_leaving_with_unsaved_changes")

    click_answer(laptop, "dismiss")
    return laptop


def a_phone_takes_over_from_the_laptop_which_does_not_answer(studio, laptop) -> None:
    """A phone opens the editor, asks to take over and continue, and the laptop lets its
    timer run out."""
    phone = studio.phone("/editor", held="upright")
    wait_for_message(phone, "another-editor-has-unsaved-changes")
    studio.shot(phone, "phone_another_editor_has_unsaved_changes")

    tap_answer(phone, "take-over-and-continue")
    wait_for_message(phone, "waiting-for-the-other-editor")
    wait_for_message(laptop, "asked-to-hand-over")
    studio.shot(laptop, "desktop_asked_to_hand_over")

    wait_for_timer_stage(laptop, "soon")
    studio.shot(laptop, "desktop_asked_to_hand_over_half_the_time_left")
    wait_for_timer_stage(laptop, "now")
    studio.shot(laptop, "desktop_asked_to_hand_over_time_running_out")

    wait_for_message(laptop, "taken-over", LONGER_THAN_THE_TAKE_OVER_TIMER_MS)
    studio.shot(laptop, "desktop_taken_over")

    # Both go away. The phone had the changes, still unsaved: they stay on the server.
    wait_until_it_is_the_editor(phone)
    close_the_tab(phone, laptop)


def a_laptop_finds_the_draft_that_was_left(studio) -> None:
    laptop = studio.laptop("/editor")
    wait_for_message(laptop, "draft-left-behind")
    studio.shot(laptop, "desktop_draft_left_behind")
    close_the_tab(laptop)   # it leaves without choosing: the draft stays


def a_phone_in_its_editing_screen_is_asked_by_a_laptop(studio):
    """A phone resumes the draft and goes on editing. A laptop asks to take over and discard;
    the phone refuses. Returns the phone, still the editor in use, with unsaved changes."""
    phone = studio.phone("/editor", held="sideways")
    wait_for_message(phone, "draft-left-behind")
    tap_answer(phone, "resume")
    wait_until_it_is_the_editor(phone)
    open_the_editing_screen_and_change_something(phone)

    phone.locator("#home-button").tap()
    wait_for_message(phone, "leaving-with-unsaved-changes")
    studio.shot(phone, "phone_leaving_with_unsaved_changes")
    tap_answer(phone, "dismiss")

    laptop = studio.laptop("/editor")
    wait_for_message(laptop, "another-editor-has-unsaved-changes")
    studio.shot(laptop, "desktop_another_editor_has_unsaved_changes")

    click_answer(laptop, "take-over-and-discard")
    wait_for_message(laptop, "waiting-for-the-other-editor")
    studio.shot(laptop, "desktop_waiting_for_the_other_editor")
    wait_for_message(phone, "asked-to-hand-over")
    studio.shot(phone, "phone_asked_to_hand_over")

    tap_answer(phone, "refuse")
    wait_for_message(laptop, "take-over-refused")
    return phone


def the_phone_loses_the_server(studio, phone) -> None:
    studio.server.stop()
    wait_for_message(phone, "connection-lost")
    studio.shot(phone, "phone_connection_lost")


def take(studio) -> None:
    """Play every scene, in order."""
    laptop = a_laptop_asks_before_leaving(studio)
    a_phone_takes_over_from_the_laptop_which_does_not_answer(studio, laptop)
    a_laptop_finds_the_draft_that_was_left(studio)
    phone = a_phone_in_its_editing_screen_is_asked_by_a_laptop(studio)
    the_phone_loses_the_server(studio, phone)
