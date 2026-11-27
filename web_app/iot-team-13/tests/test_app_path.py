"""The path the app is served at.

The whole app lives under one path, "/iot-team-13", on a laptop and online alike. The path is
one setting of the server (config.py), and these tests are about that setting: what answers
where, and that it can be changed in one place.

They use a plain client, which asks for exactly the address it is given. (The usual client of
the tests puts the app's path in front by itself; see conftest.py.)
"""
from dataclasses import replace

import pytest
from werkzeug.test import Client

from server.app import create_app
from server.config import ServerConfig


def plain_client(config):
    return Client(create_app(config))


def test_the_app_is_served_at_iot_team_13():
    assert ServerConfig().app_path == "/iot-team-13"


@pytest.mark.parametrize("address, words_on_the_page", [
    ("/iot-team-13/", "Smart Screen"),
    ("/iot-team-13/editor", "Display editor"),
    ("/iot-team-13/device", "Smart Screen: the device"),
])
def test_the_pages_are_under_the_apps_path(config, address, words_on_the_page):
    response = plain_client(config).get(address)
    assert response.status_code == 200
    assert words_on_the_page in response.get_data(as_text=True)


def test_the_files_and_the_api_are_under_the_apps_path(config, default_layout):
    client = plain_client(config)
    assert client.get("/iot-team-13/static/css/display.css").status_code == 200
    assert client.get("/iot-team-13/api/layout").get_json()["layout"] == default_layout
    assert client.get("/iot-team-13/api/events").status_code == 400   # it is there, and asks who is listening


@pytest.mark.parametrize("address", [
    "/editor", "/device", "/static/css/display.css", "/api/layout", "/api/catalog", "/api/events?role=home",
    "/api/editing/enter",
])
def test_nothing_of_the_app_answers_outside_its_path(config, address):
    assert plain_client(config).get(address).status_code == 404


def test_the_bare_address_forwards_to_the_app(config):
    response = plain_client(config).get("/")
    assert response.status_code in (301, 302, 307, 308)
    assert response.headers["Location"] == "/iot-team-13/"


def test_the_apps_path_without_its_last_slash_forwards_to_the_home_page(config):
    # The pages' addresses are relative, and "static/css/home.css" is only right when the home
    # page's own address ends with a slash.
    response = plain_client(config).get("/iot-team-13")
    assert response.status_code in (301, 308)
    assert response.headers["Location"].endswith("/iot-team-13/")


def test_api_answers_are_never_stored_and_pages_are_asked_about_under_the_path_too(config):
    client = plain_client(config)
    assert client.get("/iot-team-13/api/layout").headers["Cache-Control"] == "no-store"
    assert client.get("/iot-team-13/editor").headers["Cache-Control"] == "no-cache"


@pytest.mark.parametrize("another_path", ["/somewhere-else", "/deeper/place", "/with-a-slash-at-the-end/"])
def test_the_path_is_changed_in_one_place(config, another_path, default_layout):
    client = plain_client(replace(config, app_path=another_path))
    served_at = another_path.rstrip("/")

    assert client.get(f"{served_at}/editor").status_code == 200
    assert client.get(f"{served_at}/api/layout").get_json()["layout"] == default_layout
    assert client.get(f"{served_at}/static/js/common/grid.js").status_code == 200
    assert client.get("/").headers["Location"] == f"{served_at}/"
    assert client.get("/iot-team-13/editor").status_code == 404   # the usual path is not special


def test_an_empty_path_puts_the_app_at_the_top_of_the_address(config, default_layout):
    client = plain_client(replace(config, app_path=""))
    assert "Smart Screen" in client.get("/").get_data(as_text=True)   # the home page itself, not a forward
    assert client.get("/editor").status_code == 200
    assert client.get("/api/layout").get_json()["layout"] == default_layout
    assert client.get("/api/layout").headers["Cache-Control"] == "no-store"
