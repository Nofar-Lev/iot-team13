"""The widget catalog file is well formed, and its helpers read it correctly."""
import pytest

from server.widget_catalog import parse_size

SETTING_KINDS = {"choice", "toggle", "text", "number"}


@pytest.mark.parametrize("text, expected", [("2x1", (2, 1)), ("4x2", (4, 2)), ("10x3", (10, 3))])
def test_parse_size_reads_columns_and_rows(text, expected):
    assert parse_size(text) == expected


@pytest.mark.parametrize("not_a_size", ["", "2", "2x", "x2", "0x1", "2x0", "2 x 1", "2X1", "-2x1", None, 21, ["2x1"]])
def test_parse_size_refuses_anything_else(not_a_size):
    assert parse_size(not_a_size) is None


def test_catalog_grid_is_six_by_four(catalog):
    assert (catalog.grid_columns, catalog.grid_rows) == (6, 4)


def test_catalog_has_six_backgrounds_with_unique_ids(catalog):
    backgrounds = catalog.raw["backgrounds"]
    assert len(backgrounds) == 6
    assert len(catalog.background_ids) == 6


def test_widget_lookup(catalog):
    assert catalog.widget("clock")["name"] == "Clock"
    assert catalog.widget("no_such_widget") is None


def test_widget_types_are_unique(catalog):
    types = [entry["type"] for entry in catalog.raw["widgets"]]
    assert len(types) == len(set(types))


def test_every_widget_size_fits_the_grid(catalog):
    for entry in catalog.raw["widgets"]:
        assert entry["sizes"], f"{entry['type']} has no sizes"
        for size in entry["sizes"]:
            width, height = parse_size(size)
            assert width <= catalog.grid_columns and height <= catalog.grid_rows


def test_every_setting_is_complete_and_its_default_is_allowed(catalog):
    for entry in catalog.raw["widgets"]:
        keys = [setting["key"] for setting in entry["settings"]]
        assert len(keys) == len(set(keys)), f"{entry['type']} repeats a setting key"

        for setting in entry["settings"]:
            where = f"{entry['type']}.{setting['key']}"
            assert setting["kind"] in SETTING_KINDS, where
            assert setting["label"], where

            default = setting["default"]
            if setting["kind"] == "choice":
                assert default in [choice["value"] for choice in setting["choices"]], where
            elif setting["kind"] == "toggle":
                assert isinstance(default, bool), where
            elif setting["kind"] == "text":
                assert 0 < len(default) <= setting["max_length"], where
            elif setting["kind"] == "number":
                assert setting["min"] <= default <= setting["max"], where


def test_visible_when_points_at_a_real_setting_of_the_same_widget(catalog):
    for entry in catalog.raw["widgets"]:
        keys = {setting["key"] for setting in entry["settings"]}
        for setting in entry["settings"]:
            for other_key in setting.get("visible_when", {}):
                assert other_key in keys, f"{entry['type']}.{setting['key']}"
