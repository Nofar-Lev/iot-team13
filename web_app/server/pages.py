"""Serves the three pages and the files they load (styles, scripts, pictures, the font)."""
from __future__ import annotations

import mimetypes
from pathlib import Path

from flask import Blueprint, send_from_directory

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

# Address, the page's name, and the file that holds it.
PAGES = [
    ("/", "home", "home.html"),
    ("/editor", "editor", "editor.html"),
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

    @pages.get("/static/<path:file_path>")
    def serve_static_file(file_path: str):
        # send_from_directory refuses any path that would leave static_dir.
        return send_from_directory(static_dir, file_path)

    return pages
