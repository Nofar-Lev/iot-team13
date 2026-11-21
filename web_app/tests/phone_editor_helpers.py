"""Helpers shared by the tests of the phone editor: opening it, and touching its preview."""
import pytest

from browser_fixtures import COMMON_PHONE, sideways

playwright_api = pytest.importorskip("playwright.sync_api")
expect = playwright_api.expect


def open_phone_editor(open_page, viewport=None, tap_open=True):
    """The phone editor, as a phone gets it. With tap_open, already past the start screen."""
    editor = open_page("/editor", viewport or sideways(COMMON_PHONE), as_phone=True)
    editor.wait_for_selector("body[data-ready]")
    if tap_open:
        editor.locator("#open-editor-button").tap()
        expect(editor.locator("#editing-screen")).to_be_visible()
    return editor


def widgets_on_preview(page):
    return page.locator(".preview .display__widgets > .widget")


def preview_point(page, across: float, down: float) -> tuple:
    """A point of the preview: (0.5, 0.5) is its middle."""
    box = page.locator(".preview .display-frame").bounding_box()
    return box["x"] + box["width"] * across, box["y"] + box["height"] * down


def tap_cell(page, col: float, row: float) -> None:
    """Tap a point of the preview given in grid cells: (0.5, 0.5) is the middle of the top
    left cell, (1, 3.5) the middle of a 2x1 widget in the bottom left corner."""
    page.touchscreen.tap(*preview_point(page, col / 6, row / 4))


def tap_wherever_it_is(page, locator) -> None:
    """Tap the middle of an element, as a finger would, whatever the element says about
    itself. (The test tool refuses to tap a row that is marked as greyed out; a finger does
    not know that.)"""
    locator.scroll_into_view_if_needed()
    box = locator.bounding_box()
    page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)


def panel(page):
    return page.locator("#panel")


def shown_screen(page):
    """The element that says which screen of the layout the preview shows (data-screen)."""
    return page.locator("body")


def place_of(widget) -> list:
    """Where a widget of the preview sits, in the display's own units: [left, top]."""
    return widget.evaluate("element => [element.style.left, element.style.top]")
