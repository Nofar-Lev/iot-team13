"""Starts the real server for a test, saving layouts to a file the test chooses.

The browser tests run this as a separate program, so that they can stop the server and start
it again the way a person would.

    python3 tests/serve_with_temporary_data.py PORT PATH_OF_SAVED_LAYOUT
            [--take-over-seconds SECONDS] [--app-path PATH]

The draft is kept next to the saved layout, so it is in the test's folder too.

--take-over-seconds shortens the time an editor has to answer when another one asks to take
over, for the tests that let that time run out. --app-path serves the app at another path
than its usual one ("" for the top of the address), for the tests that check that the pages
work wherever the app is served.
"""
import argparse
import sys
from dataclasses import replace
from pathlib import Path

WEB_APP_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WEB_APP_DIR))

from server.app import create_app  # noqa: E402
from server.config import ServerConfig  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("port", type=int)
    parser.add_argument("saved_layout_path", type=Path)
    parser.add_argument("--take-over-seconds", type=float)
    parser.add_argument("--app-path")
    asked = parser.parse_args()

    config = replace(ServerConfig(), host="127.0.0.1", port=asked.port, saved_layout_path=asked.saved_layout_path)
    if asked.take_over_seconds is not None:
        config = replace(config, take_over_seconds=asked.take_over_seconds)
    if asked.app_path is not None:
        config = replace(config, app_path=asked.app_path)
    create_app(config).run(host=config.host, port=config.port, threaded=True)


if __name__ == "__main__":
    main()
