"""The rules a display layout must follow before it is saved.

A layout says which screens exist, which background each one has, and which widgets sit where.
The device trusts whatever is saved, so every rule is checked here, on the server, even though
the editor never lets the user break one.

validate_layout() returns a list of problems in plain words. An empty list means the layout is
good.
"""
from __future__ import annotations

from typing import Any

from .widget_catalog import WidgetCatalog, parse_size

LAYOUT_VERSION = 1


def validate_layout(layout: Any, catalog: WidgetCatalog) -> list[str]:
    if not isinstance(layout, dict):
        return ["The layout must be an object."]

    problems: list[str] = []
    problems += _unknown_keys(layout, {"version", "grid", "screens"}, "The layout")

    if layout.get("version") != LAYOUT_VERSION:
        problems.append(f"The layout version must be {LAYOUT_VERSION}.")

    expected_grid = {"columns": catalog.grid_columns, "rows": catalog.grid_rows}
    if layout.get("grid") != expected_grid:
        problems.append(
            f"The grid must be {catalog.grid_columns} columns by {catalog.grid_rows} rows."
        )

    screens = layout.get("screens")
    if not isinstance(screens, list):
        problems.append("The layout must have a list of screens.")
        return problems
    if not 1 <= len(screens) <= catalog.max_screens:
        problems.append(f"There must be between 1 and {catalog.max_screens} screens.")

    for screen_number, screen in enumerate(screens, start=1):
        problems += _validate_screen(screen, f"Screen {screen_number}", catalog)
    return problems


def _validate_screen(screen: Any, screen_name: str, catalog: WidgetCatalog) -> list[str]:
    if not isinstance(screen, dict):
        return [f"{screen_name} must be an object."]

    problems = _unknown_keys(screen, {"background", "widgets"}, screen_name)

    background = screen.get("background")
    if not isinstance(background, str) or background not in catalog.background_ids:
        problems.append(f"{screen_name}: the background is not in the list of backgrounds.")

    widgets = screen.get("widgets")
    if not isinstance(widgets, list):
        problems.append(f"{screen_name} must have a list of widgets.")
        return problems

    # Which widget already takes each cell, to find overlaps.
    widget_in_cell: dict[tuple[int, int], str] = {}
    for widget_number, widget in enumerate(widgets, start=1):
        widget_name = f"{screen_name}, widget {widget_number}"
        widget_problems, cells = _validate_widget(widget, widget_name, catalog)
        problems += widget_problems

        overlapped = sorted({widget_in_cell[cell] for cell in cells if cell in widget_in_cell})
        for other_widget_name in overlapped:
            problems.append(f"{widget_name} overlaps {other_widget_name}.")
        for cell in cells:
            widget_in_cell.setdefault(cell, widget_name)
    return problems


def _validate_widget(
    widget: Any, widget_name: str, catalog: WidgetCatalog
) -> tuple[list[str], list[tuple[int, int]]]:
    """Check one widget. Returns its problems and the grid cells it covers.

    The cells are empty when the widget's place could not be worked out.
    """
    if not isinstance(widget, dict):
        return [f"{widget_name} must be an object."], []

    problems = _unknown_keys(widget, {"type", "size", "col", "row", "settings"}, widget_name)

    catalog_entry = catalog.widget(widget.get("type"))
    if catalog_entry is None:
        problems.append(f"{widget_name}: there is no widget of type {widget.get('type')!r}.")
        return problems, []
    widget_name = f"{widget_name} ({catalog_entry['type']})"

    problems += _validate_settings(widget.get("settings"), catalog_entry, widget_name)

    size = widget.get("size")
    if size not in catalog_entry["sizes"]:
        problems.append(f"{widget_name}: the size {size!r} is not one of this widget's sizes.")
        return problems, []
    width, height = parse_size(size)

    column, row = widget.get("col"), widget.get("row")
    if not _is_whole_number(column) or not _is_whole_number(row):
        problems.append(f"{widget_name}: col and row must be whole numbers.")
        return problems, []

    inside_grid = (
        0 <= column
        and column + width <= catalog.grid_columns
        and 0 <= row
        and row + height <= catalog.grid_rows
    )
    if not inside_grid:
        problems.append(f"{widget_name} does not fit inside the grid.")
        return problems, []

    cells = [(column + dx, row + dy) for dx in range(width) for dy in range(height)]
    return problems, cells


def _validate_settings(settings: Any, catalog_entry: dict[str, Any], widget_name: str) -> list[str]:
    if not isinstance(settings, dict):
        return [f"{widget_name} must have a settings object."]

    allowed_keys = {setting["key"] for setting in catalog_entry["settings"]}
    problems = _unknown_keys(settings, allowed_keys, f"{widget_name} settings")

    for setting in catalog_entry["settings"]:
        key = setting["key"]
        if key not in settings:
            problems.append(f"{widget_name}: the setting {key!r} is missing.")
        elif not _setting_value_is_allowed(settings[key], setting):
            problems.append(f"{widget_name}: the setting {key!r} has a value that is not allowed.")
    return problems


def _setting_value_is_allowed(value: Any, setting: dict[str, Any]) -> bool:
    kind = setting["kind"]
    if kind == "choice":
        return value in [choice["value"] for choice in setting["choices"]]
    if kind == "toggle":
        return isinstance(value, bool)
    if kind == "text":
        return (
            isinstance(value, str)
            and value.strip() != ""
            and len(value) <= setting["max_length"]
        )
    if kind == "number":
        return _is_whole_number(value) and setting["min"] <= value <= setting["max"]
    return False


def _is_whole_number(value: Any) -> bool:
    # In Python True and False count as integers, and they are not positions or amounts.
    return isinstance(value, int) and not isinstance(value, bool)


def _unknown_keys(item: dict[str, Any], allowed_keys: set[str], item_name: str) -> list[str]:
    unknown = sorted(str(key) for key in item if key not in allowed_keys)
    return [f"{item_name} has an unknown field: {key!r}." for key in unknown]
