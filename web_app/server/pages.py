"""Serves the pages and the files they load (styles, scripts, pictures, the font)."""
from __future__ import annotations

import mimetypes
from pathlib import Path

from flask import Blueprint, request, send_from_directory

from .which_editor import editor_page_for

# Windows keeps its own list of file types, and on some machines that list says a .js file is
# plain text. Browsers refuse to run a script served as plain text, so the types are set here.
FILE_TYPES = {
    ".js": "text/javascript",
    ".css": "text/css",
    ".html": "text/html",
    ".svg": "image/svg+xml",
    ".woff2": "font/woff2",
    ".jpg": "image/jpeg",
}

# Address, the page's name, and the file that holds it. The editor is not in this list: it has
# two pages at one address, and which_editor.py chooses between them.
PAGES = [
    ("/", "home", "home.html"),
    ("/device", "device", "device.html"),
]


def create_pages(static_dir: Path) -> Blueprint:
    for extension, file_type in FILE_TYPES.items():
        mimetypes.add_type(file_type, extension)

    pages = Blueprint("pages", __name__)

    def serve_page(file_name: str):
        return lambda: send_from_directory(static_dir, file_name)

    for address, page_name, file_name in PAGES:
        pages.add_url_rule(address, endpoint=page_name, view_func=serve_page(file_name))

    @pages.get("/editor")
    def serve_the_editor():
        # The desktop editor or the phone editor, by the browser's label or by "?view=".
        file_name = editor_page_for(request.headers.get("User-Agent"), request.args.get("view"))
        response = send_from_directory(static_dir, file_name)
        # The answer depends on the browser's label, so a stored copy is good for that label only.
        response.headers["Vary"] = "User-Agent"
        return response

    @pages.get("/static/<path:file_path>")
    def serve_static_file(file_path: str):
        # send_from_directory refuses any path that would leave static_dir.
        return send_from_directory(static_dir, file_path)

    return pages
