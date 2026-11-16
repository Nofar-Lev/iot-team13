"""The three pages, driven in a real browser the way a person would use them.

These tests start the real server as a separate program (on this machine only, saving into a
temporary folder), open the pages in a browser without a window, and click, drag and type.

They need the Playwright package and its Chromium browser:

    python3 -m pip install playwright
    python3 -m playwright install chromium

Where those are not installed, the tests are skipped.
"""
import json
import re
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

playwright_api = pytest.importorskip("playwright.sync_api")
expect = playwright_api.expect

TESTS_DIR = Path(__file__).resolve().parent
DESKTOP = {"width": 1366, "height": 768}
PHONE_HELD_SIDEWAYS = {"width": 800, "height": 360}


# --- Helpers -----------------------------------------------------------------------------------

class RunningServer:
    """The real server, as a separate program that a test can stop and start again."""

    def __init__(self, saved_layout_path: Path):
        self.saved_layout_path = saved_layout_path
        self.port = self._free_port()
        self.address = f"http://127.0.0.1:{self.port}"
        self._process = None

    @staticmethod
    def _free_port() -> int:
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            return probe.getsockname()[1]

    def start(self) -> None:
        self._process = subprocess.Popen(
            [sys.executable, str(TESTS_DIR / "serve_with_temporary_data.py"),
             str(self.port), str(self.saved_layout_path)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            try:
                self.read_layout()
                return
            except OSError:
                time.sleep(0.1)
        raise RuntimeError("The test server did not start")

    def stop(self) -> None:
        if self._process is not None:
            self._process.terminate()
            self._process.wait(timeout=10)
            self._process = None

    def read_layout(self) -> dict:
        with urllib.request.urlopen(f"{self.address}/api/layout", timeout=2) as answer:
            return json.load(answer)


@pytest.fixture(scope="module")
def browser():
    with playwright_api.sync_playwright() as playwright:
        try:
            launched = playwright.chromium.launch()
        except playwright_api.Error:
            pytest.skip("Playwright's Chromium browser is not installed")
        yield launched
        launched.close()


@pytest.fixture
def server(tmp_path):
    running = RunningServer(tmp_path / "saved_layout.json")
    running.start()
    yield running
    running.stop()


@pytest.fixture
def open_page(browser, server):
    """Opens one of the pages in its own browser window. Fails the test on any page error."""
    contexts, page_errors = [], []

    def open_it(address: str, viewport: dict):
        context = browser.new_context(viewport=viewport)
        contexts.append(context)
        page = context.new_page()
        page.on("pageerror", lambda error: page_errors.append(f"{address}: {error}"))
        page.goto(server.address + address)
        return page

    yield open_it
    for context in contexts:
        context.close()
    assert page_errors == []


def open_editor(open_page):
    editor = open_page("/editor", DESKTOP)
    editor.wait_for_selector("body[data-ready]")
    return editor


def open_device(open_page):
    device = open_page("/device", PHONE_HELD_SIDEWAYS)
    device.wait_for_selector(".display .widget")
    return device


def cell_centre(page, col: float, row: float) -> tuple:
    """Where a point of the editor's display is on the page. (0.5, 0.5) is the middle of the
    top left cell."""
    box = page.locator(".editor__stage .display").bounding_box()
    return box["x"] + box["width"] * col / 6, box["y"] + box["height"] * row / 4


def drag(page, start: tuple, end: tuple) -> None:
    page.mouse.move(*start)
    page.mouse.down()
    page.mouse.move(*end, steps=8)
    page.mouse.up()


def drag_from_list(page, widget_type: str, size: str, to_col: float, to_row: float) -> None:
    entry = page.locator(f'.palette-entry[data-widget-type="{widget_type}"][data-widget-size="{size}"]')
    entry.scroll_into_view_if_needed()
    box = entry.bounding_box()
    drag(page, (box["x"] + box["width"] / 2, box["y"] + box["height"] / 2), cell_centre(page, to_col, to_row))


def widgets_on_display(page):
    return page.locator(".display__widgets > .widget")


# --- The device page ---------------------------------------------------------------------------

def test_the_device_page_draws_the_layout_and_shows_that_it_is_connected(open_page):
    device = open_device(open_page)
    expect(widgets_on_display(device)).to_have_count(4)
    expect(device.locator(".connection-icon")).to_have_attribute("data-connected", "true")


def test_the_device_page_moves_between_screens(open_page):
    device = open_device(open_page)
    device.keyboard.press("ArrowRight")
    expect(widgets_on_display(device)).to_have_count(5)
    device.keyboard.press("ArrowRight")   # there is no third screen
    expect(device.locator("body")).to_have_attribute("data-screen", "1")
    device.keyboard.press("ArrowLeft")
    expect(widgets_on_display(device)).to_have_count(4)


def test_a_swipe_on_the_device_page_shows_the_next_screen(open_page):
    device = open_device(open_page)
    drag(device, (600, 180), (300, 185))
    expect(device.locator("body")).to_have_attribute("data-screen", "1")
    drag(device, (300, 180), (600, 185))
    expect(device.locator("body")).to_have_attribute("data-screen", "0")


def test_the_display_fits_the_phone_whole(open_page):
    device = open_device(open_page)
    box = device.locator(".display-frame").bounding_box()
    assert box["x"] >= 0 and box["y"] >= 0
    assert box["x"] + box["width"] <= PHONE_HELD_SIDEWAYS["width"]
    assert box["y"] + box["height"] <= PHONE_HELD_SIDEWAYS["height"]
    assert box["width"] / box["height"] == pytest.approx(480 / 320, rel=0.01)


# --- The editor --------------------------------------------------------------------------------

def test_the_editor_starts_with_nothing_to_save(open_page):
    editor = open_editor(open_page)
    expect(widgets_on_display(editor)).to_have_count(4)
    expect(editor.locator("#save-button")).to_be_disabled()
    expect(editor.locator("#unsaved-mark")).to_be_hidden()


def test_dragging_a_widget_from_the_list_adds_it_where_it_was_dropped(open_page):
    editor = open_editor(open_page)
    drag_from_list(editor, "stock", "2x1", to_col=3, to_row=3.5)   # the free cells at the bottom

    expect(widgets_on_display(editor)).to_have_count(5)
    new_widget = editor.locator(".display__widgets > .widget--stock")
    expect(new_widget).to_have_class(re.compile("widget--selected"))   # a new widget is selected
    assert new_widget.evaluate("element => [element.style.left, element.style.top]") == ["160px", "240px"]
    expect(editor.locator("#unsaved-mark")).to_be_visible()
    expect(editor.locator("#save-button")).to_be_enabled()


def test_dropping_a_widget_on_an_occupied_place_changes_nothing(open_page):
    editor = open_editor(open_page)
    drag_from_list(editor, "stock", "2x1", to_col=3, to_row=0.5)   # on top of the large clock
    expect(widgets_on_display(editor)).to_have_count(4)
    expect(editor.locator("#unsaved-mark")).to_be_hidden()


def test_dropping_a_widget_outside_the_display_changes_nothing(open_page):
    editor = open_editor(open_page)
    entry = editor.locator('.palette-entry[data-widget-type="stock"]').bounding_box()
    start = (entry["x"] + entry["width"] / 2, entry["y"] + entry["height"] / 2)
    drag(editor, start, (start[0] + 30, start[1] + 150))   # still over the list
    expect(widgets_on_display(editor)).to_have_count(4)


def test_the_ghost_is_red_over_an_occupied_place_and_green_over_a_free_one(open_page):
    editor = open_editor(open_page)
    entry = editor.locator('.palette-entry[data-widget-type="stock"]').bounding_box()
    editor.mouse.move(entry["x"] + entry["width"] / 2, entry["y"] + entry["height"] / 2)
    editor.mouse.down()

    editor.mouse.move(*cell_centre(editor, 3, 0.5), steps=8)
    expect(editor.locator(".drop-ghost")).to_have_class("drop-ghost drop-ghost--blocked")
    editor.mouse.move(*cell_centre(editor, 3, 3.5), steps=8)
    expect(editor.locator(".drop-ghost")).to_have_class("drop-ghost drop-ghost--fits")

    editor.keyboard.press("Escape")   # give up the drag
    editor.mouse.up()
    expect(widgets_on_display(editor)).to_have_count(4)


def test_clicking_a_widget_in_the_list_adds_it_at_the_first_free_place(open_page):
    editor = open_editor(open_page)
    editor.click('.palette-entry[data-widget-type="exchange_rate"]')
    expect(widgets_on_display(editor)).to_have_count(5)
    new_widget = editor.locator(".display__widgets > .widget--exchange_rate")
    # The large clock takes the middle of the two top rows, so the first place with two free
    # cells side by side is at the start of the third row.
    assert new_widget.evaluate("element => [element.style.left, element.style.top]") == ["0px", "160px"]


def test_a_widget_can_be_moved_to_a_free_place_and_not_onto_another(open_page):
    editor = open_editor(open_page)
    weather = editor.locator(".display__widgets > .widget--weather")
    assert weather.evaluate("element => [element.style.left, element.style.top]") == ["0px", "240px"]

    drag(editor, cell_centre(editor, 1, 3.5), cell_centre(editor, 1, 2.5))   # one row up: free
    weather = editor.locator(".display__widgets > .widget--weather")
    assert weather.evaluate("element => [element.style.left, element.style.top]") == ["0px", "160px"]

    drag(editor, cell_centre(editor, 1, 2.5), cell_centre(editor, 3, 2.5))   # onto the date
    weather = editor.locator(".display__widgets > .widget--weather")
    assert weather.evaluate("element => [element.style.left, element.style.top]") == ["0px", "160px"]


def test_the_selected_widget_can_be_removed_with_its_button_or_the_delete_key(open_page):
    editor = open_editor(open_page)
    editor.mouse.click(*cell_centre(editor, 1, 3.5))   # the weather
    editor.click(".widget__remove")
    expect(widgets_on_display(editor)).to_have_count(3)

    editor.mouse.click(*cell_centre(editor, 3, 2.5))   # the date
    editor.keyboard.press("Delete")
    expect(widgets_on_display(editor)).to_have_count(2)


def test_settings_change_what_the_widget_shows(open_page):
    editor = open_editor(open_page)
    editor.mouse.click(*cell_centre(editor, 1, 3.5))   # the weather
    city = editor.locator("#setting-city")
    expect(city).to_have_value("Haifa")

    city.fill("Tel Aviv")
    expect(editor.locator(".display__widgets .weather__city")).to_have_text("Tel Aviv")
    expect(city).to_be_focused()   # typing must not throw the cursor out of the box

    editor.click('[data-setting-key="units"] button[data-value="fahrenheit"]')
    expect(editor.locator(".display__widgets .weather__temperature")).to_have_text("73°")


def test_an_emptied_text_box_keeps_the_last_good_value(open_page):
    editor = open_editor(open_page)
    editor.mouse.click(*cell_centre(editor, 1, 3.5))   # the weather
    city = editor.locator("#setting-city")
    city.fill("")
    expect(editor.locator(".display__widgets .weather__city")).to_have_text("Haifa")
    city.blur()
    expect(city).to_have_value("Haifa")


def test_the_clock_can_be_set_by_hand(open_page):
    editor = open_editor(open_page)
    editor.mouse.click(*cell_centre(editor, 3, 1))   # the large clock
    time_row = editor.locator('[data-setting-key="offset_minutes"]')
    expect(time_row).to_be_hidden()

    editor.click('[data-setting-key="time_mode"] button[data-value="manual"]')
    expect(time_row).to_be_visible()
    editor.fill("#setting-offset_minutes", "03:17")
    expect(editor.locator(".display__widgets .clock__time")).to_have_text("03:17")


def test_screens_can_be_added_given_a_background_and_removed(open_page):
    editor = open_editor(open_page)
    label = editor.locator(".screens-bar__label")
    expect(label).to_have_text("Screen 1 of 2")

    editor.click("text=Add screen")
    expect(label).to_have_text("Screen 2 of 3")
    expect(widgets_on_display(editor)).to_have_count(0)

    editor.click('.background-choice[data-background-id="night-sky"]')
    assert "night-sky.jpg" in editor.locator(".editor__stage .display").evaluate("e => e.style.backgroundImage")

    editor.click("text=Remove screen")   # an empty screen goes at the first click
    expect(label).to_have_text("Screen 2 of 2")

    editor.click("text=Remove screen")   # a screen with widgets asks for a second click
    expect(label).to_have_text("Screen 2 of 2")
    editor.click("text=Click again to remove")
    expect(label).to_have_text("Screen 1 of 1")
    expect(editor.locator(".screens-bar__actions button", has_text="Remove screen")).to_be_disabled()


def test_discard_goes_back_to_the_saved_layout(open_page):
    editor = open_editor(open_page)
    editor.click('.palette-entry[data-widget-type="stock"]')
    expect(widgets_on_display(editor)).to_have_count(5)
    editor.click("#discard-button")
    editor.click("#discard-button")   # the second click confirms
    expect(widgets_on_display(editor)).to_have_count(4)
    expect(editor.locator("#unsaved-mark")).to_be_hidden()


# --- The whole loop ----------------------------------------------------------------------------

def test_a_save_in_the_editor_redraws_the_device_by_itself(open_page, server):
    device = open_device(open_page)
    editor = open_editor(open_page)
    expect(widgets_on_display(device)).to_have_count(4)

    drag_from_list(editor, "stock", "2x1", to_col=3, to_row=3.5)
    expect(widgets_on_display(device)).to_have_count(4)   # not saved yet, so not on the device

    editor.click("#save-button")
    expect(editor.locator(".toast")).to_contain_text("The display is updating")
    expect(editor.locator("#unsaved-mark")).to_be_hidden()

    # No reload: the device page hears about the save and redraws.
    expect(widgets_on_display(device)).to_have_count(5)
    expect(device.locator(".display__widgets .stock__symbol")).to_have_text("NVDA")
    assert server.read_layout()["revision"] == 1


def test_a_saved_layout_is_what_the_editor_opens_with_next_time(open_page):
    editor = open_editor(open_page)
    editor.click('.palette-entry[data-widget-type="stock"]')
    editor.click("#save-button")
    expect(editor.locator("#unsaved-mark")).to_be_hidden()

    editor.reload()
    editor.wait_for_selector("body[data-ready]")
    expect(widgets_on_display(editor)).to_have_count(5)


def test_the_device_keeps_running_without_the_server_and_catches_up_when_it_returns(open_page, server):
    device = open_device(open_page)
    icon = device.locator(".connection-icon")
    expect(icon).to_have_attribute("data-connected", "true")

    server.stop()
    expect(icon).to_have_attribute("data-connected", "false", timeout=15_000)
    expect(widgets_on_display(device)).to_have_count(4)   # still showing its screens

    # While the device was cut off, a new layout was saved: here, by writing the file the
    # server reads when it starts.
    one_clock = {
        "version": 1,
        "grid": {"columns": 6, "rows": 4},
        "screens": [{"background": "night-sky", "widgets": [{
            "type": "clock", "size": "2x1", "col": 0, "row": 0,
            "settings": {"format": "24h", "show_seconds": False, "time_mode": "automatic", "offset_minutes": 0},
        }]}],
    }
    server.saved_layout_path.write_text(json.dumps(
        {"revision": 7, "saved_at": "2026-01-01T10:00:00+00:00", "layout": one_clock}
    ), encoding="utf-8")

    server.start()
    expect(icon).to_have_attribute("data-connected", "true", timeout=15_000)
    expect(widgets_on_display(device)).to_have_count(1)
    expect(device.locator("body")).to_have_attribute("data-revision", "7")


# --- The home page -----------------------------------------------------------------------------

def test_the_home_page_shows_the_display_and_whether_it_is_online(open_page):
    home = open_page("/", DESKTOP)
    home.wait_for_selector("body[data-ready]")
    status = home.locator("#display-status")
    expect(home.locator(".display-card__preview .display__widgets > .widget")).to_have_count(4)
    expect(status).to_have_attribute("data-state", "offline")
    expect(home.locator("#display-saved")).to_contain_text("Nothing was saved yet")

    device = open_device(open_page)
    expect(status).to_have_attribute("data-state", "online")

    device.close()
    expect(status).to_have_attribute("data-state", "offline", timeout=15_000)


def test_the_home_page_follows_a_save(open_page):
    home = open_page("/", DESKTOP)
    home.wait_for_selector("body[data-ready]")
    editor = open_editor(open_page)
    editor.click('.palette-entry[data-widget-type="stock"]')
    editor.click("#save-button")

    expect(home.locator(".display-card__preview .display__widgets > .widget")).to_have_count(5)
    expect(home.locator("#display-saved")).to_contain_text("Layout saved today at")


def test_the_edit_button_opens_the_editor(open_page):
    home = open_page("/", DESKTOP)
    home.wait_for_selector("body[data-ready]")
    home.click("#edit-button")
    home.wait_for_url("**/editor")
    home.wait_for_selector("body[data-ready]")


def test_a_sample_button_says_that_it_is_a_sample(open_page):
    home = open_page("/", DESKTOP)
    home.wait_for_selector("body[data-ready]")
    expect(home.locator(".reminder")).to_have_count(5)
    home.click("#add-reminder-button")
    expect(home.locator(".toast")).to_contain_text("sample")
