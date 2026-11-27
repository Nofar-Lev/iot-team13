"""The read-only addresses: the widget catalog and the example data."""
from __future__ import annotations

import json
from pathlib import Path

from flask import Blueprint, jsonify

from .widget_catalog import WidgetCatalog


def create_catalog_api(catalog: WidgetCatalog, demo_data_path: Path) -> Blueprint:
    catalog_api = Blueprint("catalog_api", __name__)

    with open(demo_data_path, encoding="utf-8") as demo_data_file:
        demo_data = json.load(demo_data_file)

    @catalog_api.get("/api/catalog")
    def read_catalog():
        return jsonify(catalog.raw)

    @catalog_api.get("/api/demo-data")
    def read_demo_data():
        return jsonify(demo_data)

    return catalog_api
