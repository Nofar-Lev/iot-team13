"""The pages in a real browser, with the app served at several different paths.

Every address in the pages, scripts and styles is relative, so the app works under any path
and at the top of an address. test_addresses_are_relative.py reads the files for addresses
that start with a slash; this file is the proof in a browser: a tour through the pages during
which everything they ask the server for must arrive.

All the other browser tests run under the path the app is really served at, "/iot-team-13".
"""
import pytest

from browser_fixtures import ANDROID_PHONE_LABEL, COMMON_PHONE, RunningServer, sideways

playwright_api = pytest.importorskip("playwright.sync_api")
expect = playwright_api.expect

DESKTOP = {"width": 1366, "height": 768}

AT_THE_TOP = ""
PATHS_TO_TRY = [AT_THE_TOP, "/iot-team-13", "/another-place", "/deeper/place"]


class Tour:
    """One browser window that writes down everything it asked the server for."""

    def __init__(self, browser, **window):
        self._context = browser.new_context(**window)
        self.page = self._context.new_page()
        self.asked_for = []          # the path of every request that was answered
        self.went_wrong = []         # requests that were refused, not found, or failed
        self.page.on("response", self._note_answer)
        self.page.on("requestfailed", self._note_failure)
        self.page.on("pageerror", lambda error: self.went_wrong.append(f"page error: {error}"))

    def _note_answer(self, response):
        self.asked_for.append(response.url)
        if response.status >= 400:
            self.went_wrong.append(f"{response.status} {response.url}")

    def _note_failure(self, request):
        # Leaving a page cuts its open live channel and anything still on its way. That is
        # not a failure of the address.
        if "ERR_ABORTED" not in (request.failure or ""):
            self.went_wrong.append(f"failed: {request.url} ({request.failure})")

    def asked_for_something_like(self, part_of_address: str) -> bool:
        return any(part_of_address in address for address in self.asked_for)

    def close(self):
        self._context.close()


@pytest.fixture(params=PATHS_TO_TRY, ids=lambda path: path or "at the top")
def server_at_a_path(request, tmp_path):
    running = RunningServer(tmp_path / "saved_layout.json", app_path=request.param)
    running.start()
    yield running
    running.stop()


def test_a_tour_through_the_desktop_pages_finds_everything(browser, server_at_a_path):
    server = server_at_a_path
    tour = Tour(browser, viewport=DESKTOP)
    page = tour.page

    # The bare address leads to the home page, whether it is the home page or forwards to it.
    page.goto(server.bare_address + "/")
    page.wait_for_selector("body[data-ready]")
    assert page.url == server.address + "/"
    expect(page.locator(".display__widgets > .widget")).to_have_count(4)   # the layout arrived and was drawn

    # The Edit button leads to the editor, inside the app.
    page.click("#edit-button")
    page.wait_for_selector("body[data-ready]")
    assert page.url == server.address + "/editor"
    expect(page.locator(".palette-entry").first).to_be_visible()            # the catalog arrived
    page.click('.palette-entry[data-widget-type="stock"]')                  # a change goes to the draft
    expect(page.locator("#unsaved-mark")).to_be_visible()
    page.click("#save-button")                                              # and a Save reaches the server
    expect(page.locator(".toast")).to_contain_text("Saved")
    assert server.read_layout()["revision"] == 1

    # The Home link leads back to the home page, inside the app.
    page.click("#home-link")
    page.wait_for_url(server.address + "/")
    page.wait_for_selector("body[data-ready]")
    expect(page.locator(".display__widgets > .widget")).to_have_count(5)

    # The device page.
    page.goto(server.address + "/device")
    expect(page.locator(".display .widget")).to_have_count(5)

    # The font and a background picture were really loaded, not only asked for.
    assert page.evaluate("document.fonts.check('16px Outfit')")
    assert page.evaluate("""() => new Promise((done) => {
        const address = getComputedStyle(document.querySelector('.display')).backgroundImage.slice(5, -2);
        const picture = new Image();
        picture.onload = () => done(picture.naturalWidth);
        picture.onerror = () => done(0);
        picture.src = address;
    })""") == 480

    assert tour.went_wrong == []
    for expected in ("static/css/display.css", "static/js/editor/editor_main.js", "static/fonts/Outfit-Variable.woff2",
                     "static/backgrounds/", "api/catalog", "api/layout", "api/events", "api/editing/enter",
                     "api/editing/draft", "api/editing/save"):
        assert tour.asked_for_something_like(expected), f"Nothing was asked for at {expected}"
    # Everything that was asked for was inside the app.
    outside = [address for address in tour.asked_for
               if not address.startswith(server.address + "/") and address != server.bare_address + "/"]
    assert outside == []
    tour.close()


def test_a_tour_through_the_phone_editor_finds_everything(browser, server_at_a_path):
    server = server_at_a_path
    tour = Tour(browser, viewport=sideways(COMMON_PHONE), has_touch=True, is_mobile=True, user_agent=ANDROID_PHONE_LABEL)
    page = tour.page

    page.goto(server.address + "/editor")
    page.wait_for_selector("body[data-ready]")                              # every background arrived
    page.locator("#open-editor-button").tap()
    expect(page.locator("#editing-screen")).to_be_visible()
    page.locator("#backgrounds-button").tap()
    expect(page.locator(".swatch")).to_have_count(6)

    page.locator("#panel-back-button").tap()
    page.locator("#home-button").tap()                                      # nothing unsaved: it simply leaves
    page.wait_for_url(server.address + "/")

    assert tour.went_wrong == []
    assert tour.asked_for_something_like("static/js/editor_phone/phone_editor_main.js")
    assert tour.asked_for_something_like("static/css/dialog.css")
    assert sum("static/backgrounds/" in address for address in tour.asked_for) >= 6
    assert tour.asked_for_something_like("api/editing/leave")
    tour.close()
