"""Builds the server: loads the catalog, the saved layout and the draft, and connects the addresses to them."""
from __future__ import annotations

from typing import Optional

from flask import Flask, request

from .catalog_api import create_catalog_api
from .config import ServerConfig
from .draft_store import DraftStore
from .editing_api import create_editing_api
from .events_api import create_events_api
from .layout_api import create_layout_api
from .layout_store import LayoutStore
from .layout_validation import validate_layout
from .live_updates import LiveUpdates
from .one_editor_at_a_time import OneEditorAtATime
from .pages import create_pages
from .widget_catalog import WidgetCatalog

# A layout is a few kilobytes. Anything much larger is not a layout.
LARGEST_REQUEST_BYTES = 64 * 1024


def create_app(config: Optional[ServerConfig] = None) -> Flask:
    config = config or ServerConfig()

    # static_folder=None: the pages are served by our own code, not by Flask's default.
    app = Flask(__name__, static_folder=None)
    app.config["MAX_CONTENT_LENGTH"] = LARGEST_REQUEST_BYTES

    catalog = WidgetCatalog.load(config.catalog_path)

    def problems_of(layout):
        return validate_layout(layout, catalog)

    store = LayoutStore(
        saved_layout_path=config.saved_layout_path,
        default_layout_path=config.default_layout_path,
        validator=problems_of,
    )
    drafts = DraftStore(config.draft_layout_path, validator=problems_of)

    live_updates = LiveUpdates()
    editors = OneEditorAtATime(store, drafts, live_updates, problems_of, config.take_over_seconds)

    app.register_blueprint(create_pages(config.static_dir))
    app.register_blueprint(create_catalog_api(catalog, config.demo_data_path))
    app.register_blueprint(create_layout_api(store))
    app.register_blueprint(create_editing_api(editors))
    app.register_blueprint(create_events_api(store, live_updates, editors, config.heartbeat_seconds))

    @app.after_request
    def tell_browsers_not_to_keep_old_copies(response):
        # Answers from the API are never stored. Pages and their files may be stored, but the
        # browser must ask whether they changed before using its copy, so an edit to a page
        # shows up on the next ordinary refresh.
        fresh_every_time = "no-store" if request.path.startswith("/api/") else "no-cache"
        response.headers.setdefault("Cache-Control", fresh_every_time)
        return response

    return app
