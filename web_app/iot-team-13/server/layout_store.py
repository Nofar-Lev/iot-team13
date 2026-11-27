"""Keeps the saved display layout, on disk and in memory.

Every Save gets the next revision number. A device page compares revision numbers to know
whether it is showing the newest layout.
"""
from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

# Given a layout, returns the list of what is wrong with it (empty when it is good).
LayoutValidator = Callable[[Any], list]


@dataclass(frozen=True)
class SavedLayout:
    layout: dict[str, Any]
    revision: int             # 0 means "the default layout, never saved by the user"
    saved_at: Optional[str]   # when it was saved, in UTC; None for the default layout

    def as_json(self) -> dict[str, Any]:
        return {"revision": self.revision, "saved_at": self.saved_at, "layout": self.layout}


class LayoutStore:
    def __init__(self, saved_layout_path: Path, default_layout_path: Path, validator: LayoutValidator):
        self._saved_layout_path = saved_layout_path
        self._lock = threading.Lock()
        self._current = self._load(default_layout_path, validator)

    def current(self) -> SavedLayout:
        with self._lock:
            return self._current

    def save(self, layout: dict[str, Any]) -> SavedLayout:
        """Store a layout that has already been checked, and return it with its new revision."""
        with self._lock:
            saved = SavedLayout(
                layout=layout,
                revision=self._current.revision + 1,
                saved_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            )
            self._write_file(saved)
            self._current = saved
            return saved

    def _load(self, default_layout_path: Path, validator: LayoutValidator) -> SavedLayout:
        saved = self._read_saved_file(validator)
        if saved is not None:
            return saved
        with open(default_layout_path, encoding="utf-8") as default_file:
            return SavedLayout(layout=json.load(default_file), revision=0, saved_at=None)

    def _read_saved_file(self, validator: LayoutValidator) -> Optional[SavedLayout]:
        """The layout saved earlier, or None if there is none or it can no longer be used.

        A saved file stops being usable when it is damaged, or when the widget catalog changed
        since it was saved and the layout no longer follows the rules.
        """
        try:
            with open(self._saved_layout_path, encoding="utf-8") as saved_file:
                stored = json.load(saved_file)
            layout, revision, saved_at = stored["layout"], stored["revision"], stored["saved_at"]
        except (OSError, ValueError, KeyError, TypeError):
            return None
        if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
            return None
        if not isinstance(saved_at, str):
            return None
        if validator(layout):
            return None
        return SavedLayout(layout=layout, revision=revision, saved_at=saved_at)

    def _write_file(self, saved: SavedLayout) -> None:
        # Write to a second file and then swap it in, so a crash in the middle of a Save never
        # leaves a half-written layout behind.
        self._saved_layout_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self._saved_layout_path.with_suffix(".tmp")
        with open(temporary_path, "w", encoding="utf-8") as temporary_file:
            json.dump(saved.as_json(), temporary_file, indent=2)
        os.replace(temporary_path, self._saved_layout_path)
