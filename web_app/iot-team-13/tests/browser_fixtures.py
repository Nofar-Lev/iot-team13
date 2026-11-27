"""What the browser tests share: the real server as a separate program, and browser windows.

The browser tests start the real server (on this machine only, saving into a temporary folder),
open the pages in a browser without a window, and use them the way a person would: as a desktop
browser, or as a phone with a touch screen.

They need the Playwright package and its Chromium browser:

    python3 -m pip install playwright
    python3 -m playwright install chromium

Where those are not installed, the tests that use these fixtures are skipped.

conftest.py imports the fixtures below, which is what makes them available to every test file.
"""
import json
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent

# The server's own configuration says at which path the app is served.
if str(TESTS_DIR.parent) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR.parent))
from server.config import ServerConfig  # noqa: E402

# What a phone's browser says it is. The server reads this label to tell a phone from a desktop.
ANDROID_PHONE_LABEL = (
    "Mozilla/5.0 (Linux; Android 14; SM-S911B) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/130.0.0.0 Mobile Safari/537.36"
)

# Phone screens in page units, as (width, height), with the phone held upright. The same phones
# held sideways have the two numbers the other way round.
SMALL_PHONE = (360, 780)
COMMON_PHONE = (384, 832)
LARGE_PHONE = (412, 915)
PHONES = [SMALL_PHONE, COMMON_PHONE, LARGE_PHONE]


def upright(phone: tuple) -> dict:
    """The browser window of a phone held upright."""
    return {"width": phone[0], "height": phone[1]}


def sideways(phone: tuple) -> dict:
    """The browser window of a phone held sideways."""
    return {"width": phone[1], "height": phone[0]}


class RunningServer:
    """The real server, as a separate program that a test can stop and start again."""

    def __init__(self, saved_layout_path: Path, take_over_seconds: float = None, app_path: str = None):
        self.saved_layout_path = saved_layout_path
        # None leaves the app at the path it is usually served at.
        self._app_path = app_path
        # The unsaved work of the editor in use. The file exists only while something is unsaved.
        self.draft_layout_path = saved_layout_path.with_name("draft_layout.json")
        # None leaves the server's own time for answering a take-over as it is.
        self._take_over_seconds = take_over_seconds
        self.port = self._free_port()
        # The bare address of the server, and the address of the app, which lives under a path.
        # The tests open pages at self.address + "/editor" and the like.
        self.bare_address = f"http://127.0.0.1:{self.port}"
        served_at = ServerConfig().app_path if app_path is None else app_path
        self.address = self.bare_address + served_at.rstrip("/")
        self._process = None

    @staticmethod
    def _free_port() -> int:
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            return probe.getsockname()[1]

    def start(self) -> None:
        self._process = subprocess.Popen(
            [sys.executable, str(TESTS_DIR / "serve_with_temporary_data.py"),
             str(self.port), str(self.saved_layout_path),
             *(["--take-over-seconds", str(self._take_over_seconds)] if self._take_over_seconds is not None else []),
             *(["--app-path", self._app_path] if self._app_path is not None else [])],
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

    def read_draft(self):
        """The draft the server keeps, or None when nothing is unsaved."""
        try:
            return json.loads(self.draft_layout_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None   # no draft, or the server is in the middle of writing it


@pytest.fixture(scope="module")
def browser():
    playwright_api = pytest.importorskip("playwright.sync_api")
    with playwright_api.sync_playwright() as playwright:
        try:
            launched = playwright.chromium.launch()
        except playwright_api.Error:
            pytest.skip("Playwright's Chromium browser is not installed")
        yield launched
        launched.close()


@pytest.fixture
def server(tmp_path, request):
    """The real server. A test marked with @pytest.mark.take_over_seconds(2) gets a server
    that gives an editor two seconds, not twenty, to answer a take-over."""
    marker = request.node.get_closest_marker("take_over_seconds")
    running = RunningServer(tmp_path / "saved_layout.json", take_over_seconds=marker.args[0] if marker else None)
    running.start()
    yield running
    running.stop()


def eventually(check, seconds: float = 5.0):
    """Wait until check() answers something true, and return it. Fails if it never does."""
    deadline = time.monotonic() + seconds
    while True:
        answer = check()
        if answer or time.monotonic() > deadline:
            assert answer, "It did not happen in time"
            return answer
        time.sleep(0.05)


@pytest.fixture
def open_page(browser, server):
    """Opens one of the pages in its own browser window. Fails the test on any page error.

    open_page(address, viewport) opens it as a desktop browser would.
    open_page(address, viewport, as_phone=True) opens it as a phone: a touch screen, a phone's
    way of fitting pages to its screen, and a phone's label.

    prepare(page), if given, is called before the page is opened, for a test that has to
    watch or hold back what the page fetches. wait_until says how much of the page must have
    arrived before open_page returns: "load" (everything, the usual) or "commit" (as soon as
    the server starts answering).
    """
    contexts, page_errors = [], []

    def open_it(address: str, viewport: dict, as_phone: bool = False, prepare=None, wait_until: str = "load"):
        phone_settings = (
            {"has_touch": True, "is_mobile": True, "user_agent": ANDROID_PHONE_LABEL} if as_phone else {}
        )
        context = browser.new_context(viewport=viewport, **phone_settings)
        contexts.append(context)
        page = context.new_page()
        page.on("pageerror", lambda error: page_errors.append(f"{address}: {error}"))
        if prepare:
            prepare(page)
        page.goto(server.address + address, wait_until=wait_until)
        return page

    yield open_it
    for context in contexts:
        context.close()
    assert page_errors == []


# --- A finger on a phone's screen ----------------------------------------------------------------

class Finger:
    """One finger on a phone's screen, sending real touches.

    Playwright's own mouse makes mouse events. A phone makes touch events, which the browser
    treats differently (it may take them for a scroll), so the phone tests use real touches.
    They are sent through the browser's debugging channel, which only Chromium has.

        finger = Finger(page)
        finger.down((100, 200))
        finger.rest(0.45)             # keep it still: long enough for a hold to take
        finger.move_to((300, 200))
        finger.up()
    """

    def __init__(self, page):
        self._page = page
        self._channel = page.context.new_cdp_session(page)
        self._at = None

    def _touch(self, kind: str, points: list) -> None:
        self._channel.send("Input.dispatchTouchEvent", {"type": kind, "touchPoints": points})

    def down(self, point: tuple) -> None:
        self._at = point
        self._touch("touchStart", [{"x": point[0], "y": point[1]}])

    def rest(self, seconds: float) -> None:
        """Keep the finger where it is."""
        self._page.wait_for_timeout(seconds * 1000)

    def move_to(self, point: tuple, steps: int = 8) -> None:
        start = self._at
        for step in range(1, steps + 1):
            x = start[0] + (point[0] - start[0]) * step / steps
            y = start[1] + (point[1] - start[1]) * step / steps
            self._touch("touchMove", [{"x": x, "y": y}])
        self._at = point

    def up(self) -> None:
        self._touch("touchEnd", [])
        self._at = None


def finger_swipe(page, start: tuple, end: tuple, steps: int = 8) -> None:
    """Put a finger down at start, move it to end at once, and lift it."""
    finger = Finger(page)
    finger.down(start)
    finger.move_to(end, steps)
    finger.up()


# A little longer than the time a finger must stay put for a hold to take (press_and_hold.js).
LONG_ENOUGH_TO_HOLD = 0.45


def finger_hold_and_carry(page, start: tuple, end: tuple) -> None:
    """Put a finger down at start, keep it still until the hold takes, carry to end, lift."""
    finger = Finger(page)
    finger.down(start)
    finger.rest(LONG_ENOUGH_TO_HOLD)
    finger.move_to(end)
    finger.up()
