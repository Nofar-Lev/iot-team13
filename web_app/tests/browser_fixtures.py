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
    playwright_api = pytest.importorskip("playwright.sync_api")
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
    """Opens one of the pages in its own browser window. Fails the test on any page error.

    open_page(address, viewport) opens it as a desktop browser would.
    open_page(address, viewport, as_phone=True) opens it as a phone: a touch screen, a phone's
    way of fitting pages to its screen, and a phone's label.
    """
    contexts, page_errors = [], []

    def open_it(address: str, viewport: dict, as_phone: bool = False):
        phone_settings = (
            {"has_touch": True, "is_mobile": True, "user_agent": ANDROID_PHONE_LABEL} if as_phone else {}
        )
        context = browser.new_context(viewport=viewport, **phone_settings)
        contexts.append(context)
        page = context.new_page()
        page.on("pageerror", lambda error: page_errors.append(f"{address}: {error}"))
        page.goto(server.address + address)
        return page

    yield open_it
    for context in contexts:
        context.close()
    assert page_errors == []


# --- A finger on a phone's screen ----------------------------------------------------------------

def finger_swipe(page, start: tuple, end: tuple, steps: int = 8) -> None:
    """Put a finger down at start, move it to end, and lift it, as real touches.

    Playwright's own mouse makes mouse events. A phone makes touch events, which the browser
    treats differently (it may take them for a scroll), so the phone tests use real touches.
    They are sent through the browser's debugging channel, which only Chromium has.
    """
    channel = page.context.new_cdp_session(page)

    def touch(kind: str, points: list) -> None:
        channel.send("Input.dispatchTouchEvent", {"type": kind, "touchPoints": points})

    touch("touchStart", [{"x": start[0], "y": start[1]}])
    for step in range(1, steps + 1):
        x = start[0] + (end[0] - start[0]) * step / steps
        y = start[1] + (end[1] - start[1]) * step / steps
        touch("touchMove", [{"x": x, "y": y}])
    touch("touchEnd", [])
    channel.detach()
