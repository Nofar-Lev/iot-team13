"""The widget catalog: every widget type, its allowed sizes and its settings.

The catalog is one JSON file. The editor builds its widget list and settings forms from it, and
the server checks every saved layout against it.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

SIZE_PATTERN = re.compile(r"^([1-9]\d*)x([1-9]\d*)$")


def parse_size(size: Any) -> Optional[tuple[int, int]]:
    """Turn "4x2" into (4 columns, 2 rows). Returns None if the text is not a size."""
    if not isinstance(size, str):
        return None
    match = SIZE_PATTERN.match(size)
    if match is None:
        return None
    return int(match.group(1)), int(match.group(2))


@dataclass(frozen=True)
class WidgetCatalog:
    """The catalog file, with the lookups the rest of the server needs."""

    raw: dict[str, Any]

    @classmethod
    def load(cls, path: Path) -> "WidgetCatalog":
        with open(path, encoding="utf-8") as catalog_file:
            return cls(raw=json.load(catalog_file))

    @property
    def grid_columns(self) -> int:
        return self.raw["grid"]["columns"]

    @property
    def grid_rows(self) -> int:
        return self.raw["grid"]["rows"]

    @property
    def max_screens(self) -> int:
        return self.raw["max_screens"]

    @property
    def background_ids(self) -> set[str]:
        return {background["id"] for background in self.raw["backgrounds"]}

    def widget(self, widget_type: Any) -> Optional[dict[str, Any]]:
        """The catalog entry of one widget type, or None if there is no such type."""
        for entry in self.raw["widgets"]:
            if entry["type"] == widget_type:
                return entry
        return None
