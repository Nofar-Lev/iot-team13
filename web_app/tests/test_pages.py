"""The pages and the files they load, as the server hands them out."""
import pytest


@pytest.mark.parametrize("address, words_on_the_page", [
    ("/", "Smart Screen"),
    ("/editor", "Display editor"),
    ("/device", "Smart Screen: the device"),
])
def test_each_page_is_served(client, address, words_on_the_page):
    response = client.get(address)
    assert response.status_code == 200
    assert response.content_type.startswith("text/html")
    assert words_on_the_page in response.get_data(as_text=True)


@pytest.mark.parametrize("file_path, file_type", [
    ("js/common/grid.js", "text/javascript"),
    ("css/display.css", "text/css"),
    ("fonts/Outfit-Variable.woff2", "font/woff2"),
    ("backgrounds/soft-hills.jpg", "image/jpeg"),
])
def test_files_are_served_with_the_type_a_browser_expects(client, file_path, file_type):
    # A script served as plain text is refused by browsers; some Windows machines would do that
    # if the server left the choice of type to the system.
    response = client.get(f"/static/{file_path}")
    assert response.status_code == 200
    assert response.content_type.startswith(file_type)


def test_a_missing_file_is_not_found(client):
    assert client.get("/static/js/no_such_file.js").status_code == 404


@pytest.mark.parametrize("address", [
    "/static/../server/app.py",
    "/static/..%2Fserver%2Fapp.py",
    "/static/../data/default_layout.json",
])
def test_only_files_inside_the_static_folder_are_served(client, address):
    assert client.get(address).status_code == 404


def test_the_home_page_marks_its_sample_sections(client):
    page = client.get("/").get_data(as_text=True)
    assert page.count('<span class="sample-label">Sample</span>') == 3   # the note, and two sections
    assert "show example data" in page


def test_browsers_are_told_to_check_for_newer_pages(client):
    assert client.get("/editor").headers["Cache-Control"] == "no-cache"
    assert client.get("/static/js/common/grid.js").headers["Cache-Control"] == "no-cache"


def test_browsers_are_told_never_to_store_api_answers(client):
    assert client.get("/api/layout").headers["Cache-Control"] == "no-store"
    assert client.get("/api/catalog").headers["Cache-Control"] == "no-store"
