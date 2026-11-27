"""The draft: the layout being worked on, kept on disk until it is saved or discarded."""
import json

from server.draft_store import DraftStore


def accepts_everything(layout):
    return []


def test_there_is_no_draft_to_begin_with(tmp_path):
    assert DraftStore(tmp_path / "draft_layout.json", accepts_everything).current() is None


def test_a_kept_layout_is_the_draft(tmp_path, one_clock_layout):
    drafts = DraftStore(tmp_path / "draft_layout.json", accepts_everything)
    drafts.keep(one_clock_layout)
    assert drafts.current() == one_clock_layout


def test_the_draft_is_still_there_after_a_restart(tmp_path, one_clock_layout):
    DraftStore(tmp_path / "draft_layout.json", accepts_everything).keep(one_clock_layout)
    assert DraftStore(tmp_path / "draft_layout.json", accepts_everything).current() == one_clock_layout


def test_an_erased_draft_is_gone_from_memory_and_from_disk(tmp_path, one_clock_layout):
    drafts = DraftStore(tmp_path / "draft_layout.json", accepts_everything)
    drafts.keep(one_clock_layout)
    drafts.erase()
    assert drafts.current() is None
    assert not (tmp_path / "draft_layout.json").exists()
    assert DraftStore(tmp_path / "draft_layout.json", accepts_everything).current() is None


def test_erasing_when_there_is_no_draft_is_harmless(tmp_path):
    drafts = DraftStore(tmp_path / "draft_layout.json", accepts_everything)
    drafts.erase()
    assert drafts.current() is None


def test_keeping_a_draft_creates_its_folder(tmp_path, one_clock_layout):
    drafts = DraftStore(tmp_path / "not" / "there" / "yet" / "draft_layout.json", accepts_everything)
    drafts.keep(one_clock_layout)
    assert drafts.current() == one_clock_layout


def test_no_half_written_file_is_left_beside_the_draft(tmp_path, one_clock_layout):
    DraftStore(tmp_path / "draft_layout.json", accepts_everything).keep(one_clock_layout)
    assert [path.name for path in tmp_path.iterdir()] == ["draft_layout.json"]


def test_a_damaged_draft_file_counts_as_no_draft(tmp_path):
    (tmp_path / "draft_layout.json").write_text("{ this is not JSON", encoding="utf-8")
    assert DraftStore(tmp_path / "draft_layout.json", accepts_everything).current() is None


def test_a_draft_that_no_longer_follows_the_rules_counts_as_no_draft(tmp_path, one_clock_layout):
    (tmp_path / "draft_layout.json").write_text(json.dumps(one_clock_layout), encoding="utf-8")
    refuses_everything = lambda layout: ["The catalog changed."]   # noqa: E731
    assert DraftStore(tmp_path / "draft_layout.json", refuses_everything).current() is None
