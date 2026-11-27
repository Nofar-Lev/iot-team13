"""Every address in the app's pages, scripts and styles is relative.

The app is served under a path ("/iot-team-13"). An address that starts with a slash, such as
"/api/layout" or "/static/css/home.css", points at the top of the site and so outside the
app: under a path it finds nothing. A relative address ("api/layout", "static/css/home.css")
is right wherever the app is served.

A person who tries the app only at one address cannot see this kind of mistake on every
page, so this test reads every file and looks for it. It needs no browser.

If it fails: take the first slash away. From a page or a script the address is then relative
to the page ("api/layout"); from a style sheet it is relative to the style sheet
("../fonts/...").
"""
import re
from pathlib import Path

import pytest

from server.pages import PAGES

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

# In a page: href="/..." or src="/...".
IN_A_PAGE = re.compile(r"""\b(?:href|src|action)\s*=\s*["']/""")
# In a script: a piece of text that starts with a slash and then a letter ("/api/..."), or that
# is a slash and nothing else ("/"). Text in backticks counts too.
IN_A_SCRIPT = re.compile(r"""["'`]/(?:[A-Za-z]|["'`])""")
# In a style sheet: url(/...) with or without quotes.
IN_A_STYLE_SHEET = re.compile(r"""url\(\s*["']?/""")

WHAT_TO_LOOK_FOR = {".html": IN_A_PAGE, ".js": IN_A_SCRIPT, ".css": IN_A_STYLE_SHEET}


def addresses_that_start_with_a_slash(text: str, kind: str) -> list:
    """The lines of a file's text that hold such an address, as (line number, line)."""
    looked_for = WHAT_TO_LOOK_FOR[kind]
    return [(number, line.strip()) for number, line in enumerate(text.splitlines(), start=1) if looked_for.search(line)]


def test_no_address_in_a_page_a_script_or_a_style_sheet_starts_with_a_slash():
    found = []
    files = [path for path in sorted(STATIC_DIR.rglob("*")) if path.suffix in WHAT_TO_LOOK_FOR]
    assert len(files) > 50, "The pages, scripts and styles were not found"
    for path in files:
        for number, line in addresses_that_start_with_a_slash(path.read_text(encoding="utf-8"), path.suffix):
            found.append(f"{path.relative_to(STATIC_DIR)}:{number}: {line}")
    assert found == [], (
        "These addresses start with a slash, so they point outside the app when it is served under a path. "
        "Take the first slash away:\n  " + "\n  ".join(found)
    )


@pytest.mark.parametrize("kind, text", [
    (".html", '<link rel="stylesheet" href="/static/css/home.css">'),
    (".html", '<script type="module" src="/static/js/home/home_main.js"></script>'),
    (".html", "<a href='/'>Home</a>"),
    (".js", 'const answer = await fetch("/api/layout");'),
    (".js", "source = new EventSource(`/api/events?role=${role}`);"),
    (".js", 'window.location.href = "/";'),
    (".js", "picture.src = '/static/backgrounds/' + file;"),
    (".css", 'src: url("/static/fonts/Outfit-Variable.woff2") format("woff2");'),
    (".css", "background: url(/static/backgrounds/forest.jpg);"),
])
def test_the_check_notices_each_kind_of_address_that_starts_with_a_slash(kind, text):
    assert addresses_that_start_with_a_slash(text, kind) == [(1, text)]


@pytest.mark.parametrize("kind, text", [
    (".html", '<link rel="stylesheet" href="static/css/home.css">'),
    (".html", '<a href="./">Home</a>'),
    (".html", '<a href="https://example.org/page">Elsewhere</a>'),
    (".js", 'const answer = await fetch("api/layout");'),
    (".js", 'import { el } from "../common/dom.js";'),
    (".js", "const halves = total / 2;   // divided, not an address"),
    (".js", 'const parts = date.split("-").join(" / ");'),
    (".css", 'src: url("../fonts/Outfit-Variable.woff2") format("woff2");'),
])
def test_the_check_leaves_relative_addresses_and_ordinary_code_alone(kind, text):
    assert addresses_that_start_with_a_slash(text, kind) == []


def test_every_page_sits_directly_under_the_apps_path():
    # A relative address like "static/css/home.css" is right only for a page that is one level
    # down ("/iot-team-13/editor"), not deeper ("/iot-team-13/settings/wifi").
    for address, _name, _file in PAGES + [("/editor", "editor", "")]:
        assert address.count("/") == 1, f"The page at {address} is not directly under the app's path"
