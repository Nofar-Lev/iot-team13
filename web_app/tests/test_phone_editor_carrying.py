"""Press and hold in the phone editor, with real touches in a browser set up as a phone:
moving a widget on the preview, and carrying a new one out of the panel's list.

The layout these tests start from is the one that ships with the app. On its first screen the
free cells are: columns 0 and 5 of the two top rows, columns 0-1 and 4-5 of the third row, and
columns 2-3 of the bottom row.
"""
from browser_fixtures import LONG_ENOUGH_TO_HOLD, SMALL_PHONE, Finger, finger_hold_and_carry, finger_swipe, sideways
from phone_editor_helpers import (
    expect, open_phone_editor, panel, place_of, preview_point, shown_screen, widgets_on_preview,
)

# Points of the starting layout, in grid cells: the middle of a widget, or of a free place.
THE_WEATHER = (1, 3.5)            # 2x1, bottom left
THE_DATE = (3, 2.5)               # 2x1, under the large clock
THE_ROOM = (5, 3.5)               # 2x1, bottom right
FREE_PLACE_BOTTOM_MIDDLE = (3, 3.5)
FREE_PLACE_RIGHT_OF_THE_DATE = (5, 2.5)


def at(page, cell: tuple) -> tuple:
    """Where a point given in grid cells is on the page."""
    return preview_point(page, cell[0] / 6, cell[1] / 4)


def ghost(page):
    return page.locator(".preview .carry-ghost")


def weather(page):
    return page.locator(".preview .display__widgets > .widget--weather")


def date(page):
    return page.locator(".preview .display__widgets > .widget--date")


def row_of(page, widget_type: str, size: str = None):
    by_size = f'[data-widget-size="{size}"]' if size else ""
    return page.locator(f'.widget-row[data-widget-type="{widget_type}"]{by_size}')


def middle_of(locator) -> tuple:
    locator.scroll_into_view_if_needed()
    box = locator.bounding_box()
    return box["x"] + box["width"] / 2, box["y"] + box["height"] / 2


# --- Moving a widget on the preview ---------------------------------------------------------------------

def test_a_widget_that_is_held_lifts_and_is_selected(open_page):
    editor = open_phone_editor(open_page)
    finger = Finger(editor)

    finger.down(at(editor, THE_WEATHER))
    expect(ghost(editor)).to_be_hidden()                           # not yet: the finger only just went down
    finger.rest(LONG_ENOUGH_TO_HOLD)

    # It lifted: the ghost is on the widget's own cells, and the grid is brighter.
    expect(ghost(editor)).to_be_visible()
    expect(ghost(editor)).to_have_class("carry-ghost carry-ghost--fits")
    assert [ghost(editor).get_attribute("data-col"), ghost(editor).get_attribute("data-row")] == ["0", "3"]
    expect(editor.locator(".preview .display")).to_have_class("display display--carrying")
    # It is selected from that moment, and the panel shows its options.
    expect(weather(editor)).to_have_class("widget widget--weather widget--2x1 widget--selected widget--being-moved")
    expect(panel(editor)).to_have_attribute("data-showing", "widget-options")
    expect(editor.locator(".panel__back-title")).to_have_text("Weather")

    finger.up()
    expect(ghost(editor)).to_be_hidden()
    expect(editor.locator(".preview .display")).to_have_class("display")


def test_a_held_widget_is_dropped_where_the_finger_is_lifted(open_page):
    editor = open_phone_editor(open_page)
    finger_hold_and_carry(editor, at(editor, THE_WEATHER), at(editor, FREE_PLACE_BOTTOM_MIDDLE))

    assert place_of(weather(editor)) == ["160px", "240px"]         # columns 2-3 of the bottom row
    # It stays selected after the drop, and the layout has something to save.
    expect(weather(editor)).to_have_class("widget widget--weather widget--2x1 widget--selected")
    expect(panel(editor)).to_have_attribute("data-showing", "widget-options")
    editor.locator("#panel-back-button").tap()
    expect(editor.locator("#save-button")).to_be_enabled()


def test_the_ghost_is_green_over_a_free_place_and_red_over_another_widget(open_page):
    editor = open_phone_editor(open_page)
    finger = Finger(editor)
    finger.down(at(editor, THE_WEATHER))
    finger.rest(LONG_ENOUGH_TO_HOLD)

    finger.move_to(at(editor, FREE_PLACE_BOTTOM_MIDDLE))
    expect(ghost(editor)).to_have_class("carry-ghost carry-ghost--fits")

    finger.move_to(at(editor, THE_ROOM))
    expect(ghost(editor)).to_have_class("carry-ghost carry-ghost--blocked")
    finger.up()


def test_a_widget_dropped_on_another_goes_back_to_where_it_was(open_page):
    editor = open_phone_editor(open_page)
    finger_hold_and_carry(editor, at(editor, THE_WEATHER), at(editor, THE_ROOM))

    assert place_of(weather(editor)) == ["0px", "240px"]
    expect(weather(editor)).to_have_class("widget widget--weather widget--2x1 widget--selected")


def test_a_widget_dropped_outside_the_preview_goes_back_to_where_it_was(open_page):
    editor = open_phone_editor(open_page)
    over_the_panel = middle_of(editor.locator("#panel"))
    finger_hold_and_carry(editor, at(editor, THE_WEATHER), over_the_panel)

    assert place_of(weather(editor)) == ["0px", "240px"]
    expect(widgets_on_preview(editor)).to_have_count(4)


def test_a_widget_keeps_the_part_of_it_that_was_held_under_the_finger(open_page):
    editor = open_phone_editor(open_page)
    # Held by its right half, and carried two cells to the right: it moves two cells, not three.
    finger_hold_and_carry(editor, at(editor, (1.5, 3.5)), at(editor, (3.5, 3.5)))
    assert place_of(weather(editor)) == ["160px", "240px"]


def test_holding_another_widget_switches_straight_to_that_one(open_page):
    editor = open_phone_editor(open_page)
    editor.touchscreen.tap(*at(editor, THE_WEATHER))               # the weather is selected
    expect(editor.locator(".panel__back-title")).to_have_text("Weather")

    finger = Finger(editor)
    finger.down(at(editor, THE_DATE))
    finger.rest(LONG_ENOUGH_TO_HOLD)
    expect(editor.locator(".panel__back-title")).to_have_text("Date")
    expect(editor.locator(".preview .widget--selected")).to_have_count(1)

    finger.move_to(at(editor, FREE_PLACE_RIGHT_OF_THE_DATE))
    finger.up()
    assert place_of(date(editor)) == ["320px", "160px"]


# --- What is not a hold --------------------------------------------------------------------------------------

def test_a_short_tap_selects_and_moves_nothing(open_page):
    editor = open_phone_editor(open_page)
    finger = Finger(editor)
    finger.down(at(editor, THE_WEATHER))
    finger.rest(0.1)                                               # shorter than a hold
    finger.up()

    expect(weather(editor)).to_have_class("widget widget--weather widget--2x1 widget--selected")
    expect(ghost(editor)).to_be_hidden()
    assert place_of(weather(editor)) == ["0px", "240px"]


def test_a_swipe_that_starts_on_a_widget_changes_the_screen_and_moves_nothing(open_page):
    editor = open_phone_editor(open_page)
    finger_swipe(editor, at(editor, (4.5, 1)), at(editor, (1.5, 1)))   # across the large clock, at once

    expect(shown_screen(editor)).to_have_attribute("data-screen", "1")
    editor.locator("#previous-screen-button").tap()
    expect(widgets_on_preview(editor)).to_have_count(4)
    assert place_of(editor.locator(".preview .display__widgets > .widget--clock")) == ["80px", "0px"]


def test_a_finger_that_moves_before_the_hold_takes_carries_nothing(open_page):
    editor = open_phone_editor(open_page)
    finger = Finger(editor)
    finger.down(at(editor, THE_WEATHER))
    finger.move_to(at(editor, (1, 2.9)))                           # drifts upward at once
    finger.rest(LONG_ENOUGH_TO_HOLD)
    expect(ghost(editor)).to_be_hidden()
    finger.move_to(at(editor, (1, 1.5)))
    finger.up()

    assert place_of(weather(editor)) == ["0px", "240px"]
    expect(shown_screen(editor)).to_have_attribute("data-screen", "0")   # and it was no sideways swipe either


def test_holding_an_empty_place_does_nothing(open_page):
    editor = open_phone_editor(open_page)
    finger = Finger(editor)
    finger.down(at(editor, FREE_PLACE_BOTTOM_MIDDLE))
    finger.rest(LONG_ENOUGH_TO_HOLD)
    expect(ghost(editor)).to_be_hidden()
    finger.up()
    expect(editor.locator(".preview .widget--selected")).to_have_count(0)


def test_a_hold_never_asks_the_phone_to_buzz(open_page):
    # Decided: no buzz. On the phone it was tried on, the browser gave none, and a signal that
    # sometimes comes and sometimes does not is worse than none. The lift on the screen is the signal.
    editor = open_phone_editor(open_page)
    editor.evaluate("() => { window.buzzes = 0; navigator.vibrate = () => { window.buzzes += 1; return true; }; }")
    finger_hold_and_carry(editor, at(editor, THE_WEATHER), at(editor, FREE_PLACE_BOTTOM_MIDDLE))

    assert place_of(weather(editor)) == ["160px", "240px"]
    assert editor.evaluate("window.buzzes") == 0


# --- Carrying a new widget out of the list -----------------------------------------------------------------------

def test_the_list_says_that_a_widget_can_be_held(open_page):
    editor = open_phone_editor(open_page)
    editor.locator("#add-widget-button").tap()
    expect(editor.locator(".panel__hint")).to_have_text("Tap to add. Hold to carry it to its place.")


def test_a_widget_held_in_the_list_is_carried_to_the_place_where_it_is_dropped(open_page):
    editor = open_phone_editor(open_page)
    editor.locator("#add-widget-button").tap()
    finger = Finger(editor)

    finger.down(middle_of(row_of(editor, "stock")))
    finger.rest(LONG_ENOUGH_TO_HOLD)
    # Lifted: its small picture is under the finger.
    expect(editor.locator(".carry-floating")).to_be_visible()

    finger.move_to(at(editor, FREE_PLACE_RIGHT_OF_THE_DATE))
    # Over the preview the ghost takes over from the small picture.
    expect(ghost(editor)).to_have_class("carry-ghost carry-ghost--fits")
    expect(editor.locator(".carry-floating")).to_be_hidden()
    expect(widgets_on_preview(editor)).to_have_count(4)            # not added until it is dropped

    finger.up()
    expect(widgets_on_preview(editor)).to_have_count(5)
    new_widget = widgets_on_preview(editor).nth(4)
    assert place_of(new_widget) == ["320px", "160px"]              # columns 4-5 of the third row, not the first free place
    expect(new_widget).to_have_class("widget widget--stock widget--2x1 widget--selected")
    expect(panel(editor)).to_have_attribute("data-showing", "widget-options")
    expect(editor.locator(".carry-floating")).to_have_count(0)


def test_a_new_widget_dropped_on_another_widget_is_not_added(open_page):
    editor = open_phone_editor(open_page)
    editor.locator("#add-widget-button").tap()
    finger = Finger(editor)
    finger.down(middle_of(row_of(editor, "stock")))
    finger.rest(LONG_ENOUGH_TO_HOLD)
    finger.move_to(at(editor, THE_ROOM))
    expect(ghost(editor)).to_have_class("carry-ghost carry-ghost--blocked")
    finger.up()

    expect(widgets_on_preview(editor)).to_have_count(4)
    expect(panel(editor)).to_have_attribute("data-showing", "add-widget")


def test_a_widget_that_is_held_and_let_go_over_the_list_is_not_added(open_page):
    # The touch that ends a hold must not count as a tap on the row.
    editor = open_phone_editor(open_page)
    editor.locator("#add-widget-button").tap()
    finger = Finger(editor)
    finger.down(middle_of(row_of(editor, "stock")))
    finger.rest(LONG_ENOUGH_TO_HOLD)
    finger.up()

    editor.wait_for_timeout(150)
    expect(widgets_on_preview(editor)).to_have_count(4)
    expect(panel(editor)).to_have_attribute("data-showing", "add-widget")


def test_a_tap_on_a_row_still_adds_at_the_first_free_place(open_page):
    editor = open_phone_editor(open_page)
    editor.locator("#add-widget-button").tap()
    row_of(editor, "stock").tap()

    expect(widgets_on_preview(editor)).to_have_count(5)
    assert place_of(widgets_on_preview(editor).nth(4)) == ["0px", "160px"]


def test_a_size_can_be_carried_from_the_list_of_sizes(open_page):
    editor = open_phone_editor(open_page)
    editor.locator("#add-widget-button").tap()
    row_of(editor, "clock").tap()
    finger_hold_and_carry(editor, middle_of(row_of(editor, "clock", "2x1")), at(editor, FREE_PLACE_BOTTOM_MIDDLE))

    expect(widgets_on_preview(editor)).to_have_count(5)
    new_widget = widgets_on_preview(editor).nth(4)
    assert place_of(new_widget) == ["160px", "240px"]
    expect(new_widget).to_have_class("widget widget--clock widget--2x1 widget--selected")


def test_a_widget_with_several_sizes_is_not_carried_from_the_list_of_widgets(open_page):
    # Which size to carry is not known there. A hold does nothing; a tap shows the sizes.
    editor = open_phone_editor(open_page)
    editor.locator("#add-widget-button").tap()
    finger = Finger(editor)
    finger.down(middle_of(row_of(editor, "clock")))
    finger.rest(LONG_ENOUGH_TO_HOLD)
    expect(editor.locator(".carry-floating")).to_have_count(0)
    finger.up()
    expect(widgets_on_preview(editor)).to_have_count(4)


def test_a_greyed_out_row_cannot_be_carried(open_page):
    editor = open_phone_editor(open_page)
    editor.locator("#add-widget-button").tap()
    finger = Finger(editor)
    finger.down(middle_of(row_of(editor, "reminders")))
    finger.rest(LONG_ENOUGH_TO_HOLD)
    expect(editor.locator(".carry-floating")).to_have_count(0)
    finger.up()
    expect(widgets_on_preview(editor)).to_have_count(4)


def test_a_finger_moving_on_the_list_scrolls_it_and_adds_nothing(open_page):
    editor = open_phone_editor(open_page, sideways(SMALL_PHONE))
    editor.locator("#add-widget-button").tap()
    body = editor.locator(".panel__body")
    assert body.evaluate("element => element.scrollHeight > element.clientHeight")   # the list is longer than the panel

    start = middle_of(row_of(editor, "stock"))
    finger_swipe(editor, start, (start[0], start[1] - 120))        # upward, at once
    editor.wait_for_timeout(300)

    assert body.evaluate("element => element.scrollTop") > 0
    expect(widgets_on_preview(editor)).to_have_count(4)
    expect(panel(editor)).to_have_attribute("data-showing", "add-widget")
