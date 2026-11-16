"""Where the server listens and where its files are."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

WEB_APP_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class ServerConfig:
    # "0.0.0.0" accepts connections from every network the laptop is on, which is what lets a
    # phone reach the server. To accept connections from one network only, put the laptop's
    # address on that network here (for example its address on the private network).
    host: str = "0.0.0.0"
    port: int = 8000

    # How often the live channel sends a "nothing happened" message, in seconds. It is what
    # lets a page notice within a few seconds that the server is gone, and the other way round.
    heartbeat_seconds: float = 2.0

    # Files that ship with the code: the widget catalog, the default layout, the example data.
    data_dir: Path = WEB_APP_DIR / "data"

    # The pages and everything they load.
    static_dir: Path = WEB_APP_DIR / "static"

    # The layout the user saved. Created on the first Save; kept out of the repository.
    saved_layout_path: Path = WEB_APP_DIR / "data" / "saved_layout.json"

    @property
    def catalog_path(self) -> Path:
        return self.data_dir / "widget_catalog.json"

    @property
    def default_layout_path(self) -> Path:
        return self.data_dir / "default_layout.json"

    @property
    def demo_data_path(self) -> Path:
        return self.data_dir / "demo_data.json"
