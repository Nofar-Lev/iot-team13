"""Saving and loading the layout: revisions, restarts, and files that cannot be used."""
import json

import pytest

from server.layout_store import LayoutStore
from server.layout_validation import validate_layout


@pytest.fixture
def make_store(config, catalog):
    """Builds a store the way the server does. Calling it again is like restarting the server."""
    def make():
        return LayoutStore(
            saved_layout_path=config.saved_layout_path,
            default_layout_path=config.default_layout_path,
            validator=lambda layout: validate_layout(layout, catalog),
        )
    return make


def test_before_any_save_the_default_layout_is_current(make_store, default_layout):
    current = make_store().current()
    assert current.layout == default_layout
    assert current.revision == 0
    assert current.saved_at is None


def test_nothing_is_written_until_the_first_save(make_store, config):
    make_store()
    assert not config.saved_layout_path.exists()


def test_save_makes_the_layout_current_with_revision_one(make_store, one_clock_layout):
    store = make_store()
    saved = store.save(one_clock_layout)
    assert saved.revision == 1
    assert saved.saved_at is not None
    assert store.current() == saved
    assert store.current().layout == one_clock_layout


def test_every_save_raises_the_revision_by_one(make_store, one_clock_layout):
    store = make_store()
    revisions = [store.save(one_clock_layout).revision for _ in range(3)]
    assert revisions == [1, 2, 3]


def test_a_saved_layout_survives_a_restart(make_store, one_clock_layout):
    first_run = make_store()
    first_run.save(one_clock_layout)
    saved = first_run.save(one_clock_layout)

    after_restart = make_store().current()
    assert after_restart == saved
    assert after_restart.revision == 2


def test_the_revision_keeps_counting_after_a_restart(make_store, one_clock_layout):
    make_store().save(one_clock_layout)
    assert make_store().save(one_clock_layout).revision == 2


def test_the_saved_file_is_readable_json_with_the_layout_in_it(make_store, config, one_clock_layout):
    make_store().save(one_clock_layout)
    stored = json.loads(config.saved_layout_path.read_text(encoding="utf-8"))
    assert stored["layout"] == one_clock_layout
    assert stored["revision"] == 1


def test_no_temporary_file_is_left_behind(make_store, config, one_clock_layout):
    make_store().save(one_clock_layout)
    assert [path.name for path in config.saved_layout_path.parent.iterdir()] == ["saved_layout.json"]


@pytest.mark.parametrize(
    "file_content",
    [
        "",                                                    # an empty file
        "{ this is not json",                                  # a damaged file
        "[]",                                                  # JSON, but not what we store
        '{"revision": 3, "saved_at": "2026-01-01T00:00:00"}',  # the layout is missing
        '{"layout": {}, "revision": 3, "saved_at": "2026-01-01T00:00:00"}',  # a layout that breaks the rules
    ],
)
def test_an_unusable_saved_file_falls_back_to_the_default(make_store, config, default_layout, file_content):
    config.saved_layout_path.write_text(file_content, encoding="utf-8")
    current = make_store().current()
    assert current.layout == default_layout
    assert current.revision == 0


@pytest.mark.parametrize("revision", [0, -1, "2", None, True])
def test_a_saved_file_with_a_bad_revision_falls_back_to_the_default(
    make_store, config, default_layout, one_clock_layout, revision
):
    stored = {"layout": one_clock_layout, "revision": revision, "saved_at": "2026-01-01T00:00:00+00:00"}
    config.saved_layout_path.write_text(json.dumps(stored), encoding="utf-8")
    assert make_store().current().layout == default_layout
