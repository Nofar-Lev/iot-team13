"""The layout addresses: read the saved layout, and save a new one.

A successful save is announced on the live channel, so the device redraws by itself.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from .layout_store import LayoutStore
from .layout_validation import validate_layout
from .live_updates import LiveUpdates
from .widget_catalog import WidgetCatalog


def create_layout_api(store: LayoutStore, catalog: WidgetCatalog, live_updates: LiveUpdates) -> Blueprint:
    layout_api = Blueprint("layout_api", __name__)

    @layout_api.get("/api/layout")
    def read_layout():
        return jsonify(store.current().as_json())

    @layout_api.put("/api/layout")
    def save_layout():
        layout = request.get_json(silent=True)
        if layout is None:
            return jsonify({"errors": ["The request must carry a layout as JSON."]}), 400

        problems = validate_layout(layout, catalog)
        if problems:
            return jsonify({"errors": problems}), 400

        saved = store.save(layout)
        saved_news = {"revision": saved.revision, "saved_at": saved.saved_at}
        live_updates.announce("layout", saved_news)
        return jsonify(saved_news)

    return layout_api
