"""Shared test helpers.

The tests read the catalog and the default layout that ship with the code, and write only into
a temporary folder that pytest creates and removes. They never touch a saved layout and never
use the network.
"""
import copy
import json
import sys
from dataclasses import replace
from pathlib import Path

import pytest

# Let the tests import the "server" package, wherever pytest was started from.
WEB_APP_DIR = Path(__file__).resolve().parent.parent
if str(WEB_APP_DIR) not in sys.path:
    sys.path.insert(0, str(WEB_APP_DIR))

from flask import Flask  # noqa: E402
from flask.testing import FlaskClient  # noqa: E402

from server.app import create_app  # noqa: E402
from server.config import ServerConfig  # noqa: E402
from server.widget_catalog import WidgetCatalog  # noqa: E402


class ClientInsideTheApp(FlaskClient):
    """The stand-in browser of the tests. It speaks to the app by addresses inside the app
    ("/api/layout", "/editor") and puts the path the app is served at in front of them, the
    way a browser does that opened the app at its real address. So a test reads the same
    wherever the app is served, and still goes through the real path every time.

    A test about addresses outside the app (the bare address that forwards) uses a plain
    werkzeug.test.Client, which adds nothing.
    """

    def open(self, *args, **kwargs):
        if args and isinstance(args[0], str) and args[0].startswith("/"):
            args = (self.application.config["APP_PATH"] + args[0], *args[1:])
        return super().open(*args, **kwargs)


# Every app that a test builds hands out this client from test_client().
Flask.test_client_class = ClientInsideTheApp

# The fixtures of the browser tests: the real server as a separate program, and browser windows.
# Importing them here is what lets every test file use them.
from browser_fixtures import browser, open_page, server  # noqa: E402, F401


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "take_over_seconds(seconds): how long the test's server gives an editor to answer a take-over",
    )


@pytest.fixture
def config(tmp_path):
    """The real configuration, except that saving goes to a temporary folder."""
    return replace(ServerConfig(), saved_layout_path=tmp_path / "saved_layout.json")


@pytest.fixture
def catalog(config):
    return WidgetCatalog.load(config.catalog_path)


@pytest.fixture
def default_layout(config):
    with open(config.default_layout_path, encoding="utf-8") as default_file:
        return json.load(default_file)


@pytest.fixture
def one_clock_layout():
    """The smallest useful layout: one screen with one small clock in the top left corner."""
    return copy.deepcopy(
        {
            "version": 1,
            "grid": {"columns": 6, "rows": 4},
            "screens": [
                {
                    "background": "soft-hills",
                    "widgets": [
                        {
                            "type": "clock",
                            "size": "2x1",
                            "col": 0,
                            "row": 0,
                            "settings": {
                                "format": "24h",
                                "show_seconds": False,
                                "time_mode": "automatic",
                                "offset_minutes": 0,
                            },
                        }
                    ],
                }
            ],
        }
    )


@pytest.fixture
def client(config):
    """A browser stand-in that talks to the server directly, with no network."""
    return create_app(config).test_client()
