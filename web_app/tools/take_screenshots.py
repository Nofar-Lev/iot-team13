"""Takes the screenshots that the project's documents use, from the app itself.

Run it from the web_app folder:

    python3 tools/take_screenshots.py                        every set
    python3 tools/take_screenshots.py one_editor_at_a_time   one set, or several
    python3 tools/take_screenshots.py --list                 which sets there are

Each set starts the real server on this computer only, with data of its own that is thrown
away afterwards, opens the pages in a browser without a window, uses them the way a person
would, and saves pictures into the folder of the document they belong to. Pictures of the same
name are replaced; nothing else in that folder is touched.

Run it again when the look of something in the pictures changes, and look at the new pictures
before keeping them. Every page is told that it is the same moment (studio.py), so a picture
that is taken again only differs where the app does. The exception is a picture of a running
countdown: it may catch the bar a second earlier or later.

It needs the Playwright package and its Chromium browser, like the browser tests:

    python3 -m pip install playwright pytest
    python3 -m playwright install chromium

To add a set: write a file in tools/screenshots/ with PICTURES_FOLDER (a folder inside the
repository) and take(studio), the way one_editor_at_a_time.py does, and add it to SETS below.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from screenshots import one_editor_at_a_time  # noqa: E402
from screenshots.studio import Studio  # noqa: E402

# Every set of screenshots, by the name it is asked for.
SETS = {
    "one_editor_at_a_time": one_editor_at_a_time,
}


def take_set(name: str) -> bool:
    """Take one set. Answers whether every page ran without an error."""
    screenshot_set = SETS[name]
    print(f"{name}: taking pictures into {screenshot_set.PICTURES_FOLDER}")
    with Studio(screenshot_set.PICTURES_FOLDER) as studio:
        screenshot_set.take(studio)
    for picture in studio.pictures_taken:
        print(f"  {picture}.jpg")
    for error in studio.page_errors:
        print(f"  A page reported an error: {error}")
    return not studio.page_errors


def main(arguments: list[str]) -> int:
    if arguments == ["--list"]:
        print("\n".join(SETS))
        return 0
    unknown = [name for name in arguments if name not in SETS]
    if unknown:
        print(f"There is no set called {', '.join(unknown)}. The sets are: {', '.join(SETS)}.")
        return 2
    every_set_went_well = all([take_set(name) for name in (arguments or SETS)])
    return 0 if every_set_went_well else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
