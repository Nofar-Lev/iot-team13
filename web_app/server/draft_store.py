"""Keeps the draft: the layout being worked on in the editor, before it is saved.

The draft lives next to the saved layout, on disk and in memory, so unsaved work survives a
closed tab, a lost connection and a restart of the server. There is at most one draft. "No
draft" means that nothing is unsaved.
"""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any, Optional

from .layout_store import LayoutValidator


class DraftStore:
    def __init__(self, draft_layout_path: Path, validator: LayoutValidator):
        self._draft_layout_path = draft_layout_path
        self._lock = threading.Lock()
        self._draft = self._read_file(validator)

    def current(self) -> Optional[dict[str, Any]]:
        """The draft, or None when nothing is unsaved."""
        with self._lock:
            return self._draft

    def keep(self, layout: dict[str, Any]) -> None:
        """Make a layout that has already been checked the draft."""
        with self._lock:
            self._write_file(layout)
            self._draft = layout

    def erase(self) -> None:
        with self._lock:
            self._draft = None
            try:
                os.remove(self._draft_layout_path)
            except FileNotFoundError:
                pass

    def _read_file(self, validator: LayoutValidator) -> Optional[dict[str, Any]]:
        """The draft left on disk, or None if there is none or it can no longer be used.

        A draft stops being usable when its file is damaged, or when the widget catalog
        changed since it was written and the layout no longer follows the rules.
        """
        try:
            with open(self._draft_layout_path, encoding="utf-8") as draft_file:
                layout = json.load(draft_file)
        except (OSError, ValueError):
            return None
        if validator(layout):
            return None
        return layout

    def _write_file(self, layout: dict[str, Any]) -> None:
        # Write to a second file and then swap it in, so a crash in the middle never leaves a
        # half-written draft behind.
        self._draft_layout_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self._draft_layout_path.with_suffix(".tmp")
        with open(temporary_path, "w", encoding="utf-8") as temporary_file:
            json.dump(layout, temporary_file, indent=2)
        os.replace(temporary_path, self._draft_layout_path)
