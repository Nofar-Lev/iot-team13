"""The layout address: read the saved layout, the one the device shows.

Nothing is saved here. A layout is saved by the editor in use, through the editing addresses
(editing_api.py), so that nothing can be saved from outside the rules of one editor at a time.
"""
from __future__ import annotations

from flask import Blueprint, jsonify

from .layout_store import LayoutStore


def create_layout_api(store: LayoutStore) -> Blueprint:
    layout_api = Blueprint("layout_api", __name__)

    @layout_api.get("/api/layout")
    def read_layout():
        return jsonify(store.current().as_json())

    return layout_api
