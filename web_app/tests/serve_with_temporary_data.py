"""Starts the real server for a test, saving layouts to a file the test chooses.

The browser tests run this as a separate program, so that they can stop the server and start
it again the way a person would.

    python3 tests/serve_with_temporary_data.py PORT PATH_OF_SAVED_LAYOUT [TAKE_OVER_SECONDS]

The draft is kept next to the saved layout, so it is in the test's folder too. The last
argument shortens the time an editor has to answer when another one asks to take over, for
the tests that let that time run out.
"""
import sys
from dataclasses import replace
from pathlib import Path

WEB_APP_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WEB_APP_DIR))

from server.app import create_app  # noqa: E402
from server.config import ServerConfig  # noqa: E402


def main() -> None:
    port, saved_layout_path = int(sys.argv[1]), Path(sys.argv[2])
    config = replace(ServerConfig(), host="127.0.0.1", port=port, saved_layout_path=saved_layout_path)
    if len(sys.argv) > 3:
        config = replace(config, take_over_seconds=float(sys.argv[3]))
    create_app(config).run(host=config.host, port=config.port, threaded=True)


if __name__ == "__main__":
    main()
