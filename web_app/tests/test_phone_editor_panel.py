"""What the phone editor's panel does, in a real browser set up as a phone held sideways:
adding a widget, a widget's options, the backgrounds, adding and removing screens, and saving.

The layout these tests start from is the one that ships with the app. Its first screen has a
large clock on top, the date under it, the weather in the bottom left corner and the room's
climate in the bottom right: there is room for a 2x1 widget, and none for a 2x2 or a 4x2.
"""
from browser_fixtures import SMALL_PHONE, sideways
from phone_editor_helpers import (
    expect, open_phone_editor, panel, place_of, shown_screen, tap_cell, tap_wherever_it_is, widgets_on_preview,
)

DESKTOP = {"width": 1366, "height": 768}

# Where widgets of the starting layout are, as points to tap (in grid cells).
THE_WEATHER = (1, 3.5)
THE_DATE = (3, 2.5)
THE_LARGE_CLOCK = (3, 1)
AN_EMPTY_CELL = (0.5, 0.5)


def row_of(page, widget_type: str, size: str = None):
    by_size = f'[data-widget-size="{size}"]' if size else ""
    return page.locator(f'.widget-row[data-widget-type="{widget_type}"]{by_size}')


def toast(page):
    return page.locator(".toast--showing")


# --- Adding a widget ---------------------------------------------------------------------------------

def test_add_widget_opens_the_list_of_widgets(open_page):
    editor = open_phone_editor(open_page)
    editor.locator("#add-widget-button").tap()

    expect(panel(editor)).to_have_attribute("data-showing", "add-widget")
    expect(editor.locator(".widget-row")).to_have_count(7)
    expect(editor.locator(".widget-row__name")).to_have_text(
        ["Clock", "Date", "Weather", "Stock", "Exchange rate", "Room climate", "Today's reminders"]
    )
    # Every row carries a small picture of the widget.
    expect(editor.locator(".widget-row .widget-picture")).to_have_count(7)

    editor.locator("#panel-back-button").tap()
    expect(panel(editor)).to_have_attribute("data-showing", "main-menu")


def test_a_tap_on_a_widget_with_one_size_adds_it_at_the_first_free_place(open_page):
    editor = open_phone_editor(open_page)
    editor.locator("#add-widget-button").tap()
    row_of(editor, "date").tap()

    expect(widgets_on_preview(editor)).to_have_count(5)
    new_widget = widgets_on_preview(editor).nth(4)
    assert place_of(new_widget) == ["0px", "160px"]          # the first free place: column 0, row 2
    expect(new_widget).to_have_class("widget widget--date widget--2x1 widget--selected")


def test_after_adding_the_panel_shows_the_new_widgets_options(open_page):
    editor = open_phone_editor(open_page)
    editor.locator("#add-widget-button").tap()
    row_of(editor, "stock").tap()

    expect(panel(editor)).to_have_attribute("data-showing", "widget-options")
    expect(editor.locator(".panel__back-title")).to_have_text("Stock")
    expect(editor.locator(".panel__top-note")).to_have_text("2 × 1")
    expect(editor.locator("#setting-symbol")).to_have_value("NVDA")


def test_a_widget_with_several_sizes_asks_for_the_size_first(open_page):
    editor = open_phone_editor(open_page)
    editor.locator("#add-widget-button").tap()
    expect(row_of(editor, "clock").locator(".widget-row__note")).to_have_text("2 sizes ›")
    row_of(editor, "clock").tap()

    expect(panel(editor)).to_have_attribute("data-showing", "widget-sizes")
    expect(editor.locator(".panel__back-title")).to_have_text("Clock")
    expect(editor.locator(".widget-row__name")).to_have_text(["Small", "Large"])
    expect(widgets_on_preview(editor)).to_have_count(4)        # nothing was added yet

    row_of(editor, "clock", "2x1").tap()
    expect(widgets_on_preview(editor)).to_have_count(5)
    expect(widgets_on_preview(editor).nth(4)).to_have_class("widget widget--clock widget--2x1 widget--selected")


def test_a_size_with_no_room_is_greyed_out_and_a_tap_on_it_only_says_so(open_page):
    editor = open_phone_editor(open_page)
    editor.locator("#add-widget-button").tap()
    row_of(editor, "clock").tap()

    large = row_of(editor, "clock", "4x2")
    expect(large).to_have_class("widget-row widget-row--no-room")
    expect(large).to_have_attribute("aria-disabled", "true")
    expect(large.locator(".widget-row__note")).to_have_text("No room")
    expect(row_of(editor, "clock", "2x1")).to_have_attribute("aria-disabled", "false")

    tap_wherever_it_is(editor, large)
    expect(toast(editor)).to_have_text("This screen has no room for that widget.")
    expect(widgets_on_preview(editor)).to_have_count(4)
    expect(panel(editor)).to_have_attribute("data-showing", "widget-sizes")


def test_a_widget_with_no_room_in_any_size_is_greyed_out_in_the_list(open_page):
    editor = open_phone_editor(open_page)
    editor.locator("#add-widget-button").tap()

    reminders = row_of(editor, "reminders")                    # its only size is 4x2
    expect(reminders).to_have_attribute("aria-disabled", "true")
    # The weather has room in one of its two sizes, so its row is not greyed out.
    expect(row_of(editor, "weather")).to_have_attribute("aria-disabled", "false")

    tap_wherever_it_is(editor, reminders)
    expect(toast(editor)).to_have_text("This screen has no room for that widget.")
    expect(widgets_on_preview(editor)).to_have_count(4)


def test_what_has_room_follows_the_screen_that_is_showing(open_page):
    editor = open_phone_editor(open_page)
    editor.locator("#add-widget-button").tap()
    row_of(editor, "weather").tap()
    expect(row_of(editor, "weather", "2x2")).to_have_attribute("aria-disabled", "true")

    editor.locator("#next-screen-button").tap()                # the second screen has a free 2x2
    expect(panel(editor)).to_have_attribute("data-showing", "widget-sizes")
    expect(row_of(editor, "weather", "2x2")).to_have_attribute("aria-disabled", "false")


def test_back_from_the_sizes_returns_to_the_list_and_then_to_the_main_menu(open_page):
    editor = open_phone_editor(open_page)
    editor.locator("#add-widget-button").tap()
    row_of(editor, "weather").tap()

    editor.locator("#panel-back-button").tap()
    expect(panel(editor)).to_have_attribute("data-showing", "add-widget")
    editor.locator("#panel-back-button").tap()
    expect(panel(editor)).to_have_attribute("data-showing", "main-menu")


# --- A widget's options --------------------------------------------------------------------------------

def test_a_tap_on_a_widget_selects_it_and_shows_its_options(open_page):
    editor = open_phone_editor(open_page)
    tap_cell(editor, *THE_WEATHER)

    expect(editor.locator(".preview .widget--weather")).to_have_class("widget widget--weather widget--2x1 widget--selected")
    expect(panel(editor)).to_have_attribute("data-showing", "widget-options")
    expect(editor.locator(".panel__back-title")).to_have_text("Weather")
    expect(editor.locator("#setting-city")).to_have_value("Haifa")
    # Save and Discard belong to the main menu only.
    expect(editor.locator("#save-button")).to_have_count(0)
    expect(editor.locator(".panel__foot")).to_be_hidden()


def test_an_option_changes_the_preview_as_it_is_changed(open_page):
    editor = open_phone_editor(open_page)
    tap_cell(editor, *THE_WEATHER)

    editor.locator("#setting-city").fill("Tel Aviv")
    expect(editor.locator(".preview .weather__city")).to_have_text("Tel Aviv")
    expect(editor.locator("#setting-city")).to_be_focused()    # the box was not rebuilt while typing

    editor.locator('.choice-row__button[data-value="fahrenheit"]').tap()
    expect(editor.locator(".preview .weather__temperature")).to_have_text("73°")
    # The widget is still the selected one.
    expect(editor.locator(".preview .widget--weather")).to_have_class("widget widget--weather widget--2x1 widget--selected")


def test_a_tap_outside_the_widget_lets_go_of_it_and_returns_to_the_main_menu(open_page):
    editor = open_phone_editor(open_page)
    tap_cell(editor, *THE_WEATHER)
    tap_cell(editor, *AN_EMPTY_CELL)

    expect(editor.locator(".preview .widget--selected")).to_have_count(0)
    expect(panel(editor)).to_have_attribute("data-showing", "main-menu")


def test_a_tap_beside_the_preview_also_lets_go(open_page):
    editor = open_phone_editor(open_page)
    tap_cell(editor, *THE_WEATHER)

    dots = editor.locator("#screen-dots").bounding_box()       # under the preview, not on it
    editor.touchscreen.tap(dots["x"] + 20, dots["y"] + dots["height"] / 2)
    expect(editor.locator(".preview .widget--selected")).to_have_count(0)
    expect(panel(editor)).to_have_attribute("data-showing", "main-menu")


def test_a_tap_on_another_widget_moves_the_selection_to_it(open_page):
    editor = open_phone_editor(open_page)
    tap_cell(editor, *THE_WEATHER)
    tap_cell(editor, *THE_DATE)

    expect(editor.locator(".preview .widget--selected")).to_have_count(1)
    expect(editor.locator(".preview .widget--date")).to_have_class("widget widget--date widget--2x1 widget--selected")
    expect(editor.locator(".panel__back-title")).to_have_text("Date")


def test_back_lets_go_of_the_widget(open_page):
    editor = open_phone_editor(open_page)
    tap_cell(editor, *THE_WEATHER)
    editor.locator("#panel-back-button").tap()

    expect(editor.locator(".preview .widget--selected")).to_have_count(0)
    expect(panel(editor)).to_have_attribute("data-showing", "main-menu")


def test_opening_a_menu_while_a_widget_is_selected_is_not_possible_without_letting_go(open_page):
    # The main menu's buttons are not there while a widget's options are showing.
    editor = open_phone_editor(open_page)
    tap_cell(editor, *THE_WEATHER)
    expect(editor.locator("#add-widget-button")).to_have_count(0)
    expect(editor.locator("#backgrounds-button")).to_have_count(0)


def test_remove_widget_removes_it_at_once(open_page):
    editor = open_phone_editor(open_page)
    tap_cell(editor, *THE_WEATHER)
    editor.locator(".settings__remove").tap()

    expect(widgets_on_preview(editor)).to_have_count(3)
    expect(editor.locator(".preview .widget--weather")).to_have_count(0)
    expect(panel(editor)).to_have_attribute("data-showing", "main-menu")


def test_every_option_of_the_widget_with_the_most_options_can_be_reached_on_a_small_phone(open_page):
    viewport = sideways(SMALL_PHONE)
    editor = open_phone_editor(open_page, viewport)
    tap_cell(editor, *THE_LARGE_CLOCK)
    expect(editor.locator(".panel__back-title")).to_have_text("Clock")

    for control in [".choice-row__button[data-value='12h']", ".switch", ".choice-row__button[data-value='manual']",
                    ".settings__remove"]:
        element = editor.locator(control)
        element.scroll_into_view_if_needed()
        box = element.bounding_box()
        assert box["y"] >= 0 and box["y"] + box["height"] <= viewport["height"], control
        assert box["x"] + box["width"] <= viewport["width"], control
    # The panel's own page never scrolls sideways.
    assert editor.evaluate("(() => { const b = document.querySelector('.panel__body'); return b.scrollWidth <= b.clientWidth; })()")


# --- Backgrounds -----------------------------------------------------------------------------------------

def test_backgrounds_shows_the_six_as_named_swatches_with_the_current_one_marked(open_page):
    editor = open_phone_editor(open_page)
    editor.locator("#backgrounds-button").tap()

    expect(panel(editor)).to_have_attribute("data-showing", "backgrounds")
    expect(editor.locator(".panel__back-title")).to_have_text("Backgrounds")
    expect(editor.locator(".swatch")).to_have_text(
        ["Soft hills", "Night sky", "Calm sea", "Morning mist", "Lavender", "Forest"]
    )
    expect(editor.locator(".swatch--current")).to_have_text("Soft hills")
    # The six fit without scrolling.
    assert editor.evaluate("(() => { const b = document.querySelector('.panel__body'); return b.scrollHeight <= b.clientHeight; })()")


def test_a_tap_on_a_swatch_changes_the_background_at_once(open_page):
    editor = open_phone_editor(open_page)
    editor.locator("#backgrounds-button").tap()
    editor.locator('.swatch[data-background-id="night-sky"]').tap()

    assert "night-sky.jpg" in editor.locator(".preview .display").evaluate("element => element.style.backgroundImage")
    expect(editor.locator(".swatch--current")).to_have_text("Night sky")
    expect(panel(editor)).to_have_attribute("data-showing", "backgrounds")   # still here, to try another


def test_each_screen_has_its_own_background(open_page):
    editor = open_phone_editor(open_page)
    editor.locator("#backgrounds-button").tap()
    editor.locator("#next-screen-button").tap()
    expect(editor.locator(".swatch--current")).to_have_text("Calm sea")


# --- Adding and removing screens -----------------------------------------------------------------------------

def test_the_plus_arrow_adds_a_screen_and_shows_it(open_page):
    editor = open_phone_editor(open_page)
    editor.locator("#next-screen-button").tap()                # to the last screen
    editor.locator("#next-screen-button").tap()                # the arrow is now a "+"

    expect(editor.locator(".screen-dots__dot")).to_have_count(3)
    expect(shown_screen(editor)).to_have_attribute("data-screen", "2")
    expect(widgets_on_preview(editor)).to_have_count(0)
    expect(editor.locator("#save-button")).to_be_enabled()


def test_an_empty_screen_is_removed_at_once(open_page):
    editor = open_phone_editor(open_page)
    editor.locator("#next-screen-button").tap()
    editor.locator("#next-screen-button").tap()                # a new, empty third screen

    editor.locator("#remove-screen-button").tap()
    expect(editor.locator(".screen-dots__dot")).to_have_count(2)
    expect(shown_screen(editor)).to_have_attribute("data-screen", "1")


def test_a_screen_with_widgets_is_removed_only_after_a_second_tap(open_page):
    editor = open_phone_editor(open_page)
    remove = editor.locator("#remove-screen-button")

    remove.tap()
    expect(remove).to_have_text("Tap again to remove")
    expect(remove).to_have_class("quiet-action button--danger")
    expect(editor.locator(".screen-dots__dot")).to_have_count(2)   # nothing removed yet

    remove.tap()
    expect(editor.locator(".screen-dots__dot")).to_have_count(1)
    expect(widgets_on_preview(editor)).to_have_count(5)            # what was the second screen
    # The only screen left cannot be removed.
    expect(remove).to_have_text("Remove this screen")
    expect(remove).to_be_disabled()


def test_doing_something_else_drops_the_question(open_page):
    editor = open_phone_editor(open_page)
    remove = editor.locator("#remove-screen-button")
    remove.tap()
    expect(remove).to_have_text("Tap again to remove")

    editor.locator("#next-screen-button").tap()                    # look at the other screen instead
    expect(remove).to_have_text("Remove this screen")
    expect(editor.locator(".screen-dots__dot")).to_have_count(2)


# --- Saving, discarding, leaving --------------------------------------------------------------------------------

def add_a_date_and_return_to_the_main_menu(editor):
    editor.locator("#add-widget-button").tap()
    row_of(editor, "date").tap()
    editor.locator("#panel-back-button").tap()
    expect(panel(editor)).to_have_attribute("data-showing", "main-menu")


def test_save_layout_sends_the_layout_to_the_server(open_page, server):
    editor = open_phone_editor(open_page)
    add_a_date_and_return_to_the_main_menu(editor)
    expect(editor.locator("#save-button")).to_be_enabled()

    editor.locator("#save-button").tap()
    expect(toast(editor)).to_contain_text("Saved.")
    expect(editor.locator("#save-button")).to_be_disabled()
    expect(editor.locator("#discard-button")).to_be_disabled()

    saved = server.read_layout()
    assert saved["revision"] == 1
    assert [widget["type"] for widget in saved["layout"]["screens"][0]["widgets"]] == [
        "clock", "date", "weather", "room_climate", "date",
    ]


def test_what_the_phone_saved_is_what_the_desktop_editor_opens(open_page):
    editor = open_phone_editor(open_page)
    add_a_date_and_return_to_the_main_menu(editor)
    editor.locator("#save-button").tap()
    expect(toast(editor)).to_contain_text("Saved.")

    desktop_editor = open_page("/editor", DESKTOP)
    desktop_editor.wait_for_selector("body[data-ready]")
    expect(desktop_editor.locator(".display__widgets > .widget")).to_have_count(5)


def test_discard_asks_for_a_second_tap_and_then_undoes_the_changes(open_page):
    editor = open_phone_editor(open_page)
    add_a_date_and_return_to_the_main_menu(editor)
    discard = editor.locator("#discard-button")

    discard.tap()
    expect(discard).to_have_text("Tap again")
    expect(widgets_on_preview(editor)).to_have_count(5)            # nothing undone yet

    discard.tap()
    expect(widgets_on_preview(editor)).to_have_count(4)
    expect(discard).to_have_text("Discard")
    expect(discard).to_be_disabled()
    expect(editor.locator("#save-button")).to_be_disabled()


def test_home_asks_before_leaving_with_unsaved_changes(open_page):
    editor = open_phone_editor(open_page)
    add_a_date_and_return_to_the_main_menu(editor)
    home = editor.locator("#home-button")

    home.tap()
    expect(home).to_have_text("Tap again to leave")
    expect(editor.locator("#editing-screen")).to_be_visible()      # still in the editor

    home.tap()
    editor.wait_for_url("**/")
    editor.wait_for_selector(".home-page")
