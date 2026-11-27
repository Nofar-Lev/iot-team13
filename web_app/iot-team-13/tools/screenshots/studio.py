"""Where screenshots are taken: the app running on its own, and browser windows to look at it.

The studio starts the real server as a separate program, on this computer only, saving into a
folder of its own that is thrown away afterwards. It never touches the saved layout of the
real app. The browser has no window.

A set of screenshots (one file next to this one) gets a studio, opens pages in it, uses them
the way a person would, and calls shot() where a picture is wanted.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

WEB_APP_DIR = Path(__file__).resolve().parent.parent.parent   # web_app/iot-team-13
REPOSITORY_DIR = WEB_APP_DIR.parent.parent

# The tests already know how to run the real server as a separate program, and what a phone's
# browser says it is. The studio uses the same code, so the two cannot drift apart.
sys.path.insert(0, str(WEB_APP_DIR / "tests"))
from browser_fixtures import ANDROID_PHONE_LABEL, COMMON_PHONE, RunningServer, sideways, upright  # noqa: E402

# Every page is told that it is this moment, always. The display's clock and date then look
# the same in every picture and every time the pictures are taken again, so a retaken picture
# only differs where the app does. Timers and countdowns still run as usual.
THE_TIME_IN_EVERY_PICTURE = "2026-03-10T10:30:00"

# A laptop's window, and how sharp its pictures are. Larger numbers make larger files.
LAPTOP_WINDOW = {"width": 1280, "height": 720}
LAPTOP_SHARPNESS = 1.25
PHONE_SHARPNESS = 2

JPEG_QUALITY = 82

# How long a page gets to settle before its picture is taken (a dialog fading in, a toast).
SETTLE_BEFORE_A_PICTURE_MS = 400


class Studio:
    """Use it with "with": the server and the browser are stopped when the block ends.

    pictures_folder: where shot() saves, as a path inside the repository.
    """

    def __init__(self, pictures_folder: str):
        self.pictures_folder = REPOSITORY_DIR / pictures_folder
        self.pictures_taken: list[str] = []
        self.page_errors: list[str] = []
        self.server: RunningServer = None

    def __enter__(self) -> "Studio":
        # Playwright is asked for only here, so that the list of sets can be read without it.
        from playwright.sync_api import sync_playwright

        self._data_folder = tempfile.TemporaryDirectory(prefix="smart-screen-screenshots-")
        self.server = RunningServer(Path(self._data_folder.name) / "saved_layout.json")
        self.server.start()
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch()
        self.pictures_folder.mkdir(parents=True, exist_ok=True)
        return self

    def __exit__(self, *exception) -> None:
        self._browser.close()
        self._playwright.stop()
        self.server.stop()
        self._data_folder.cleanup()

    # ---- Opening pages -------------------------------------------------------------------

    def laptop(self, address: str):
        """Open one of the app's pages (for example "/editor") as a laptop's browser would."""
        return self._open(address, viewport=LAPTOP_WINDOW, device_scale_factor=LAPTOP_SHARPNESS)

    def phone(self, address: str, held: str = "upright"):
        """Open one of the app's pages as a phone would, held "upright" or "sideways".

        A phone in the studio does not turn by itself. A scene that wants the phone editor's
        editing screen opens the phone sideways from the start.
        """
        viewport = sideways(COMMON_PHONE) if held == "sideways" else upright(COMMON_PHONE)
        return self._open(
            address, viewport=viewport, device_scale_factor=PHONE_SHARPNESS,
            has_touch=True, is_mobile=True, user_agent=ANDROID_PHONE_LABEL,
        )

    def _open(self, address: str, **window):
        page = self._browser.new_context(**window).new_page()
        page.on("pageerror", lambda error: self.page_errors.append(f"{address}: {error}"))
        page.clock.set_fixed_time(THE_TIME_IN_EVERY_PICTURE)
        page.goto(self.server.address + address)
        return page

    # ---- Taking pictures -----------------------------------------------------------------

    def shot(self, page, name: str) -> None:
        """Save a picture of the page as <name>.jpg in the set's folder."""
        page.wait_for_timeout(SETTLE_BEFORE_A_PICTURE_MS)
        page.screenshot(path=str(self.pictures_folder / f"{name}.jpg"), type="jpeg", quality=JPEG_QUALITY)
        self.pictures_taken.append(name)
