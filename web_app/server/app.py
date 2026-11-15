"""Builds the server: loads the catalog and the layout, and connects the addresses to them."""
from __future__ import annotations

from typing import Optional

from flask import Flask

from .catalog_api import create_catalog_api
from .config import ServerConfig
from .layout_api import create_layout_api
from .layout_store import LayoutStore
from .layout_validation import validate_layout
from .widget_catalog import WidgetCatalog

# A layout is a few kilobytes. Anything much larger is not a layout.
LARGEST_REQUEST_BYTES = 64 * 1024


def create_app(config: Optional[ServerConfig] = None) -> Flask:
    config = config or ServerConfig()

    # static_folder=None: the pages are served by our own code, not by Flask's default.
    app = Flask(__name__, static_folder=None)
    app.config["MAX_CONTENT_LENGTH"] = LARGEST_REQUEST_BYTES

    catalog = WidgetCatalog.load(config.catalog_path)
    store = LayoutStore(
        saved_layout_path=config.saved_layout_path,
        default_layout_path=config.default_layout_path,
        validator=lambda layout: validate_layout(layout, catalog),
    )

    app.register_blueprint(create_catalog_api(catalog, config.demo_data_path))
    app.register_blueprint(create_layout_api(store, catalog))
    return app
