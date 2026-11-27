"""The rules of the display editor: one editor in use at a time, and how another takes over.

The rules are tried here directly, with no pages and no network. Time is a clock that moves
only when a test says so, so the take-over timer is tried without waiting.
"""
import copy

import pytest

from live_channel import waiting_news
from server.draft_store import DraftStore
from server.layout_store import LayoutStore
from server.layout_validation import validate_layout
from server.live_updates import LiveUpdates
from server.one_editor_at_a_time import (
    EditorNotConnected,
    LayoutNotAccepted,
    NoTakeOverToAnswer,
    NotTheEditorInUse,
    OneEditorAtATime,
)

TAKE_OVER_SECONDS = 20


class ClockTheTestMoves:
    """Stands in for the real timers: time passes only when a test calls advance()."""

    def __init__(self):
        self._now = 0.0
        self._waiting = []   # [when it is due, what to call]

    def now(self):
        return self._now

    def call_after(self, seconds, callback):
        timer = [self._now + seconds, callback]
        self._waiting.append(timer)
        return lambda: self._waiting.remove(timer) if timer in self._waiting else None

    def timers_waiting(self):
        return len(self._waiting)

    def advance(self, seconds):
        self._now += seconds
        for timer in [timer for timer in self._waiting if timer[0] <= self._now]:
            self._waiting.remove(timer)
            timer[1]()


class Desk:
    """Everything one test needs: the saved layout, the draft, the live channel and the rules."""

    def __init__(self, config, catalog):
        self._config = config
        self._problems_of = lambda layout: validate_layout(layout, catalog)
        self.clock = ClockTheTestMoves()
        self.live_updates = LiveUpdates()
        self.restart()

    def restart(self):
        """What a restart of the server does: read the files again, and forget who was editing."""
        self.store = LayoutStore(self._config.saved_layout_path, self._config.default_layout_path, self._problems_of)
        self.drafts = DraftStore(self._config.draft_layout_path, self._problems_of)
        self.editors = OneEditorAtATime(
            self.store, self.drafts, self.live_updates, self._problems_of, TAKE_OVER_SECONDS, timers=self.clock)

    def open_editor(self):
        """A newly opened editor page: connected, and not yet the editor in use."""
        return self.live_updates.add_listener("editor")

    def close(self, editor):
        """What happens when an editor page goes away."""
        self.live_updates.remove_listener(editor)
        self.editors.leave(editor.id)

    def editor_in_use(self):
        """An editor that entered and is the one in use, with nothing unsaved."""
        editor = self.open_editor()
        assert self.editors.enter(editor.id)["situation"] == "editing"
        return editor


@pytest.fixture
def desk(config, catalog):
    return Desk(config, catalog)


@pytest.fixture
def changed_layout(one_clock_layout):
    """A good layout that differs from the saved one."""
    return one_clock_layout


@pytest.fixture
def changed_again_layout(one_clock_layout):
    layout = copy.deepcopy(one_clock_layout)
    layout["screens"][0]["widgets"][0]["col"] = 3
    return layout


@pytest.fixture
def editor_with_unsaved_changes(desk, changed_layout):
    """The editor in use, with a draft."""
    editor = desk.editor_in_use()
    desk.editors.update_draft(editor.id, changed_layout)
    waiting_news(editor)
    return editor


def may_edit(desk, editor, layout):
    """Whether the server lets this editor change the draft."""
    try:
        desk.editors.update_draft(editor.id, layout)
        return True
    except NotTheEditorInUse:
        return False


# ---- Opening the editor when nobody else has it ------------------------------------------

def test_the_first_editor_starts_from_the_saved_layout(desk, default_layout):
    editor = desk.open_editor()
    assert desk.editors.enter(editor.id) == {
        "situation": "editing",
        "saved": {"revision": 0, "saved_at": None, "layout": default_layout},
        "draft": None,
    }


def test_an_editor_must_be_connected_to_enter(desk):
    gone = desk.open_editor()
    desk.close(gone)
    for editor_id in (gone.id, "made-up-id", desk.live_updates.add_listener("home").id):
        with pytest.raises(EditorNotConnected):
            desk.editors.enter(editor_id)


def test_entering_twice_changes_nothing(desk):
    editor = desk.open_editor()
    assert desk.editors.enter(editor.id) == desk.editors.enter(editor.id)
    assert waiting_news(editor) == []


def test_after_the_editor_in_use_left_with_nothing_unsaved_the_next_one_just_starts(desk):
    desk.close(desk.editor_in_use())
    assert desk.editors.enter(desk.open_editor().id)["situation"] == "editing"


# ---- A draft that was left behind --------------------------------------------------------

def test_a_new_editor_is_asked_about_a_draft_that_was_left_behind(desk, editor_with_unsaved_changes, changed_layout):
    desk.close(editor_with_unsaved_changes)
    new = desk.open_editor()
    assert desk.editors.enter(new.id) == {"situation": "draft_left_behind"}
    assert not may_edit(desk, new, changed_layout)   # it is not the editor in use until it chooses
    assert desk.drafts.current() == changed_layout


def test_a_draft_survives_a_restart_of_the_server_and_is_asked_about(desk, editor_with_unsaved_changes, changed_layout):
    desk.close(editor_with_unsaved_changes)
    desk.restart()
    new = desk.open_editor()
    assert desk.editors.enter(new.id) == {"situation": "draft_left_behind"}
    assert desk.editors.answer_about_the_draft_left_behind(new.id, keep_changes=True)["draft"] == changed_layout


def test_resuming_a_draft_continues_from_it(desk, editor_with_unsaved_changes, changed_layout, default_layout, changed_again_layout):
    desk.close(editor_with_unsaved_changes)
    new = desk.open_editor()
    desk.editors.enter(new.id)
    answer = desk.editors.answer_about_the_draft_left_behind(new.id, keep_changes=True)
    assert answer["situation"] == "editing"
    assert answer["draft"] == changed_layout
    assert answer["saved"]["layout"] == default_layout
    assert may_edit(desk, new, changed_again_layout)


def test_discarding_a_draft_that_was_left_behind_starts_from_the_saved_layout(desk, editor_with_unsaved_changes, default_layout):
    desk.close(editor_with_unsaved_changes)
    new = desk.open_editor()
    desk.editors.enter(new.id)
    answer = desk.editors.answer_about_the_draft_left_behind(new.id, keep_changes=False)
    assert answer == {
        "situation": "editing",
        "saved": {"revision": 0, "saved_at": None, "layout": default_layout},
        "draft": None,
    }
    assert desk.drafts.current() is None


def test_an_editor_that_goes_home_without_choosing_leaves_the_draft_as_it_is(desk, editor_with_unsaved_changes, changed_layout):
    desk.close(editor_with_unsaved_changes)
    undecided = desk.open_editor()
    desk.editors.enter(undecided.id)
    desk.close(undecided)
    assert desk.drafts.current() == changed_layout
    assert desk.editors.enter(desk.open_editor().id) == {"situation": "draft_left_behind"}


def test_when_two_editors_are_asked_about_a_draft_the_second_to_choose_meets_the_first(
        desk, editor_with_unsaved_changes, changed_layout):
    desk.close(editor_with_unsaved_changes)
    first, second = desk.open_editor(), desk.open_editor()
    desk.editors.enter(first.id)
    desk.editors.enter(second.id)

    assert desk.editors.answer_about_the_draft_left_behind(first.id, keep_changes=True)["situation"] == "editing"

    # The second one chose Discard, but the draft is no longer "left behind": the first has it.
    answer = desk.editors.answer_about_the_draft_left_behind(second.id, keep_changes=False)
    assert answer == {"situation": "another_editor_has_unsaved_changes"}
    assert desk.drafts.current() == changed_layout


# ---- Another editor is in use, with nothing unsaved --------------------------------------

def test_a_new_editor_takes_over_at_once_from_one_with_nothing_unsaved(desk, changed_layout):
    old = desk.editor_in_use()
    new = desk.open_editor()

    assert desk.editors.enter(new.id)["situation"] == "editing"

    assert waiting_news(old) == [("taken_over", {"changes": "none"})]
    assert not may_edit(desk, old, changed_layout)
    assert may_edit(desk, new, changed_layout)


# ---- Another editor is in use, with unsaved changes --------------------------------------

def test_a_new_editor_is_told_when_another_has_unsaved_changes(desk, editor_with_unsaved_changes, changed_again_layout):
    old, new = editor_with_unsaved_changes, desk.open_editor()
    assert desk.editors.enter(new.id) == {"situation": "another_editor_has_unsaved_changes"}
    assert waiting_news(old) == []                       # nothing happened yet, so it is not told
    assert may_edit(desk, old, changed_again_layout)     # and it goes on editing
    assert not may_edit(desk, new, changed_again_layout)


def test_a_new_editor_that_goes_home_does_not_disturb_the_old_one(desk, editor_with_unsaved_changes, changed_again_layout):
    old, new = editor_with_unsaved_changes, desk.open_editor()
    desk.editors.enter(new.id)
    desk.close(new)
    assert waiting_news(old) == []
    assert may_edit(desk, old, changed_again_layout)


@pytest.mark.parametrize("keep_changes", [True, False])
def test_asking_to_take_over_asks_the_old_editor_and_starts_the_timer(desk, editor_with_unsaved_changes, keep_changes):
    old, new = editor_with_unsaved_changes, desk.open_editor()
    desk.editors.enter(new.id)

    answer = desk.editors.ask_to_take_over(new.id, keep_changes)

    assert answer == {"situation": "waiting_for_the_other_editor", "seconds": TAKE_OVER_SECONDS}
    assert waiting_news(old) == [("take_over_request", {"keep_changes": keep_changes, "seconds": TAKE_OVER_SECONDS})]
    assert waiting_news(new) == []


def test_the_old_editor_goes_on_editing_while_it_is_asked(desk, editor_with_unsaved_changes, changed_again_layout):
    old, new = editor_with_unsaved_changes, desk.open_editor()
    desk.editors.ask_to_take_over(new.id, keep_changes=True)
    assert may_edit(desk, old, changed_again_layout)
    assert not may_edit(desk, new, changed_again_layout)


def test_an_approved_take_over_that_continues_carries_the_draft_over(
        desk, editor_with_unsaved_changes, changed_layout, changed_again_layout, default_layout):
    old, new = editor_with_unsaved_changes, desk.open_editor()
    desk.editors.ask_to_take_over(new.id, keep_changes=True)
    waiting_news(old)

    desk.editors.approve_take_over(old.id)

    assert desk.clock.timers_waiting() == 0
    assert waiting_news(old) == [("taken_over", {"changes": "carried_over"})]
    assert waiting_news(new) == [("take_over_granted", {
        "situation": "editing",
        "saved": {"revision": 0, "saved_at": None, "layout": default_layout},
        "draft": changed_layout,
    })]
    assert not may_edit(desk, old, changed_again_layout)
    assert may_edit(desk, new, changed_again_layout)


def test_an_approved_take_over_that_discards_erases_the_draft(desk, editor_with_unsaved_changes):
    old, new = editor_with_unsaved_changes, desk.open_editor()
    desk.editors.ask_to_take_over(new.id, keep_changes=False)
    waiting_news(old)

    desk.editors.approve_take_over(old.id)

    assert waiting_news(old) == [("taken_over", {"changes": "discarded"})]
    [(name, details)] = waiting_news(new)
    assert (name, details["situation"], details["draft"]) == ("take_over_granted", "editing", None)
    assert desk.drafts.current() is None


@pytest.mark.parametrize("keep_changes, what_became_of_the_changes", [(True, "carried_over"), (False, "discarded")])
def test_no_answer_in_time_counts_as_approval(desk, editor_with_unsaved_changes, changed_layout,
                                              keep_changes, what_became_of_the_changes):
    old, new = editor_with_unsaved_changes, desk.open_editor()
    desk.editors.ask_to_take_over(new.id, keep_changes)
    waiting_news(old)

    desk.clock.advance(TAKE_OVER_SECONDS - 0.1)
    assert waiting_news(old) == [] and waiting_news(new) == []   # not yet

    desk.clock.advance(0.1)
    assert waiting_news(old) == [("taken_over", {"changes": what_became_of_the_changes})]
    [(name, details)] = waiting_news(new)
    assert name == "take_over_granted"
    assert details["draft"] == (changed_layout if keep_changes else None)
    assert not may_edit(desk, old, changed_layout)


def test_a_refused_take_over_leaves_everything_as_it_was(desk, editor_with_unsaved_changes, changed_layout, changed_again_layout):
    old, new = editor_with_unsaved_changes, desk.open_editor()
    desk.editors.ask_to_take_over(new.id, keep_changes=False)
    waiting_news(old)

    desk.editors.refuse_take_over(old.id)

    assert waiting_news(new) == [("take_over_refused", {})]
    assert waiting_news(old) == []
    assert desk.drafts.current() == changed_layout
    assert may_edit(desk, old, changed_again_layout)
    assert not may_edit(desk, new, changed_layout)


def test_the_timer_of_a_refused_take_over_never_goes_off(desk, editor_with_unsaved_changes, changed_layout):
    old, new = editor_with_unsaved_changes, desk.open_editor()
    desk.editors.ask_to_take_over(new.id, keep_changes=False)
    desk.editors.refuse_take_over(old.id)
    waiting_news(old), waiting_news(new)
    assert desk.clock.timers_waiting() == 0

    desk.clock.advance(10 * TAKE_OVER_SECONDS)

    assert waiting_news(old) == [] and waiting_news(new) == []
    assert desk.drafts.current() == changed_layout


def test_after_a_refusal_the_new_editor_can_ask_again(desk, editor_with_unsaved_changes):
    old, new = editor_with_unsaved_changes, desk.open_editor()
    desk.editors.ask_to_take_over(new.id, keep_changes=True)
    desk.editors.refuse_take_over(old.id)
    assert desk.editors.enter(new.id) == {"situation": "another_editor_has_unsaved_changes"}
    assert desk.editors.ask_to_take_over(new.id, keep_changes=True)["situation"] == "waiting_for_the_other_editor"


@pytest.mark.parametrize("how_it_leaves", ["says so", "its page closes"])
def test_when_the_new_editor_leaves_the_question_disappears(desk, editor_with_unsaved_changes, changed_layout,
                                                             changed_again_layout, how_it_leaves):
    old, new = editor_with_unsaved_changes, desk.open_editor()
    desk.editors.ask_to_take_over(new.id, keep_changes=False)
    waiting_news(old)

    if how_it_leaves == "says so":
        desk.editors.leave(new.id)   # "Return to home": its channel is still open for a moment
    else:
        desk.close(new)

    assert waiting_news(old) == [("take_over_withdrawn", {})]
    assert desk.clock.timers_waiting() == 0      # the timer is gone with it
    desk.clock.advance(10 * TAKE_OVER_SECONDS)
    assert waiting_news(old) == []
    assert desk.drafts.current() == changed_layout
    assert may_edit(desk, old, changed_again_layout)


def test_a_bystander_that_leaves_disturbs_nobody(desk, editor_with_unsaved_changes, changed_again_layout):
    old, bystander = editor_with_unsaved_changes, desk.open_editor()
    desk.editors.enter(bystander.id)
    desk.editors.leave(bystander.id)
    desk.editors.leave("made-up-id")
    assert waiting_news(old) == []
    assert may_edit(desk, old, changed_again_layout)


@pytest.mark.parametrize("keep_changes", [True, False])
def test_when_the_old_editor_goes_away_while_asked_the_new_one_is_not_kept_waiting(
        desk, editor_with_unsaved_changes, changed_layout, keep_changes):
    old, new = editor_with_unsaved_changes, desk.open_editor()
    desk.editors.ask_to_take_over(new.id, keep_changes)

    desk.close(old)

    [(name, details)] = waiting_news(new)
    assert name == "take_over_granted"
    assert details["draft"] == (changed_layout if keep_changes else None)
    assert may_edit(desk, new, changed_layout)


def test_the_waiting_editor_can_ask_how_long_is_left(desk, editor_with_unsaved_changes):
    new = desk.open_editor()
    desk.editors.ask_to_take_over(new.id, keep_changes=True)
    desk.clock.advance(5)
    assert desk.editors.enter(new.id) == {"situation": "waiting_for_the_other_editor", "seconds": TAKE_OVER_SECONDS - 5}
    assert desk.editors.ask_to_take_over(new.id, keep_changes=True)["seconds"] == TAKE_OVER_SECONDS - 5


# ---- A third editor while a take-over waits for its answer -------------------------------

def test_a_third_editor_is_told_that_a_take_over_is_in_progress(desk, editor_with_unsaved_changes, changed_layout):
    old, new, third = editor_with_unsaved_changes, desk.open_editor(), desk.open_editor()
    desk.editors.ask_to_take_over(new.id, keep_changes=True)
    waiting_news(old)

    in_progress = {"situation": "take_over_in_progress"}
    assert desk.editors.enter(third.id) == in_progress
    assert desk.editors.ask_to_take_over(third.id, keep_changes=False) == in_progress
    assert desk.editors.answer_about_the_draft_left_behind(third.id, keep_changes=False) == in_progress

    # None of that disturbed the two that are in the middle of it.
    assert waiting_news(old) == [] and waiting_news(new) == []
    assert desk.drafts.current() == changed_layout
    desk.editors.approve_take_over(old.id)
    assert waiting_news(new)[0][0] == "take_over_granted"


def test_a_third_editor_can_try_again_once_the_take_over_is_settled(desk, editor_with_unsaved_changes):
    old, new, third = editor_with_unsaved_changes, desk.open_editor(), desk.open_editor()
    desk.editors.ask_to_take_over(new.id, keep_changes=True)
    assert desk.editors.enter(third.id) == {"situation": "take_over_in_progress"}
    desk.editors.approve_take_over(old.id)
    assert desk.editors.enter(third.id) == {"situation": "another_editor_has_unsaved_changes"}


# ---- Answers that come from the wrong editor, or too late --------------------------------

def test_only_the_editor_that_was_asked_can_answer(desk, editor_with_unsaved_changes):
    old, new, third = editor_with_unsaved_changes, desk.open_editor(), desk.open_editor()
    desk.editors.ask_to_take_over(new.id, keep_changes=False)
    for not_asked in (new, third):
        with pytest.raises(NoTakeOverToAnswer):
            desk.editors.approve_take_over(not_asked.id)
        with pytest.raises(NoTakeOverToAnswer):
            desk.editors.refuse_take_over(not_asked.id)
    assert desk.editors.enter(new.id)["situation"] == "waiting_for_the_other_editor"


def test_an_answer_with_no_question_is_refused(desk, editor_with_unsaved_changes):
    with pytest.raises(NoTakeOverToAnswer):
        desk.editors.approve_take_over(editor_with_unsaved_changes.id)
    with pytest.raises(NoTakeOverToAnswer):
        desk.editors.refuse_take_over(editor_with_unsaved_changes.id)


def test_a_refusal_that_comes_after_the_time_ran_out_is_too_late(desk, editor_with_unsaved_changes, changed_layout):
    old, new = editor_with_unsaved_changes, desk.open_editor()
    desk.editors.ask_to_take_over(new.id, keep_changes=True)
    desk.clock.advance(TAKE_OVER_SECONDS)
    with pytest.raises(NoTakeOverToAnswer):
        desk.editors.refuse_take_over(old.id)
    assert may_edit(desk, new, changed_layout)


# ---- The situation changed between the question and the choice ---------------------------

@pytest.mark.parametrize("keep_changes", [True, False])
def test_taking_over_from_an_editor_that_left_in_the_meantime_still_follows_the_choice(
        desk, editor_with_unsaved_changes, changed_layout, keep_changes):
    old, new = editor_with_unsaved_changes, desk.open_editor()
    desk.editors.enter(new.id)
    desk.close(old)

    answer = desk.editors.ask_to_take_over(new.id, keep_changes)

    assert answer["situation"] == "editing"
    assert answer["draft"] == (changed_layout if keep_changes else None)
    assert desk.drafts.current() == (changed_layout if keep_changes else None)


def test_taking_over_from_an_editor_that_saved_in_the_meantime_happens_at_once(desk, editor_with_unsaved_changes, changed_layout):
    old, new = editor_with_unsaved_changes, desk.open_editor()
    desk.editors.enter(new.id)
    desk.editors.save(old.id)
    waiting_news(old)

    answer = desk.editors.ask_to_take_over(new.id, keep_changes=False)

    assert answer["situation"] == "editing"
    assert answer["saved"]["layout"] == changed_layout   # what the old editor saved is not touched
    assert waiting_news(old) == [("taken_over", {"changes": "none"})]


def test_an_editor_that_saved_while_it_was_asked_loses_nothing_to_a_discarding_take_over(
        desk, editor_with_unsaved_changes, changed_layout):
    old, new = editor_with_unsaved_changes, desk.open_editor()
    desk.editors.ask_to_take_over(new.id, keep_changes=False)
    desk.editors.save(old.id)
    waiting_news(old), waiting_news(new)

    desk.editors.approve_take_over(old.id)

    assert waiting_news(old) == [("taken_over", {"changes": "none"})]
    assert desk.store.current().layout == changed_layout


# ---- The draft ---------------------------------------------------------------------------

def test_a_change_becomes_the_draft_and_the_saved_layout_stays(desk, changed_layout, default_layout):
    editor = desk.editor_in_use()
    assert desk.editors.update_draft(editor.id, changed_layout) == {"has_unsaved_changes": True}
    assert desk.drafts.current() == changed_layout
    assert desk.store.current().layout == default_layout
    assert desk.store.current().revision == 0


def test_a_change_back_to_the_saved_layout_leaves_nothing_unsaved(desk, changed_layout, default_layout):
    editor = desk.editor_in_use()
    desk.editors.update_draft(editor.id, changed_layout)
    assert desk.editors.update_draft(editor.id, default_layout) == {"has_unsaved_changes": False}
    assert desk.drafts.current() is None
    # So the next editor is not held up by it.
    assert desk.editors.enter(desk.open_editor().id)["situation"] == "editing"


def test_a_layout_that_breaks_the_rules_does_not_become_the_draft(desk, changed_layout, changed_again_layout):
    editor = desk.editor_in_use()
    desk.editors.update_draft(editor.id, changed_layout)
    changed_again_layout["screens"][0]["widgets"][0]["col"] = 99
    with pytest.raises(LayoutNotAccepted) as refusal:
        desk.editors.update_draft(editor.id, changed_again_layout)
    assert refusal.value.problems
    assert desk.drafts.current() == changed_layout


def test_an_editor_that_never_entered_cannot_touch_anything(desk, editor_with_unsaved_changes, changed_layout, changed_again_layout):
    stranger = desk.open_editor()
    for forbidden in (
        lambda: desk.editors.update_draft(stranger.id, changed_again_layout),
        lambda: desk.editors.save(stranger.id),
        lambda: desk.editors.discard(stranger.id),
    ):
        with pytest.raises(NotTheEditorInUse):
            forbidden()
    assert desk.drafts.current() == changed_layout
    assert desk.store.current().revision == 0


def test_an_editor_that_was_taken_over_cannot_save_or_discard(desk, editor_with_unsaved_changes, changed_layout):
    old, new = editor_with_unsaved_changes, desk.open_editor()
    desk.editors.ask_to_take_over(new.id, keep_changes=True)
    desk.clock.advance(TAKE_OVER_SECONDS)

    with pytest.raises(NotTheEditorInUse):
        desk.editors.save(old.id)
    with pytest.raises(NotTheEditorInUse):
        desk.editors.discard(old.id)

    assert desk.store.current().revision == 0
    assert desk.drafts.current() == changed_layout


# ---- Save and Discard --------------------------------------------------------------------

def test_saving_makes_the_draft_the_saved_layout_and_tells_every_page(desk, changed_layout):
    home, device = desk.live_updates.add_listener("home"), desk.live_updates.add_listener("device")
    editor = desk.editor_in_use()
    desk.editors.update_draft(editor.id, changed_layout)
    waiting_news(home), waiting_news(device), waiting_news(editor)

    answer = desk.editors.save(editor.id)

    assert answer["revision"] == 1 and answer["saved_at"]
    assert desk.store.current().layout == changed_layout
    assert desk.drafts.current() is None
    for listener in (home, device, editor):
        assert waiting_news(listener) == [("layout", answer)]


def test_the_editor_goes_on_editing_after_a_save(desk, changed_layout, changed_again_layout):
    editor = desk.editor_in_use()
    desk.editors.update_draft(editor.id, changed_layout)
    desk.editors.save(editor.id)
    assert desk.editors.update_draft(editor.id, changed_again_layout) == {"has_unsaved_changes": True}
    assert desk.editors.save(editor.id)["revision"] == 2


def test_saving_with_nothing_unsaved_changes_nothing(desk):
    home = desk.live_updates.add_listener("home")
    editor = desk.editor_in_use()
    assert desk.editors.save(editor.id) == {"revision": 0, "saved_at": None}
    assert waiting_news(home) == []


def test_discarding_erases_the_draft_and_answers_with_the_saved_layout(desk, editor_with_unsaved_changes, default_layout, changed_layout):
    editor = editor_with_unsaved_changes
    assert desk.editors.discard(editor.id) == {
        "situation": "editing",
        "saved": {"revision": 0, "saved_at": None, "layout": default_layout},
        "draft": None,
    }
    assert desk.drafts.current() is None
    assert may_edit(desk, editor, changed_layout)   # it is still the editor in use


def test_a_draft_that_equals_the_saved_layout_is_dropped_when_the_server_starts(desk, default_layout):
    # This is what is left if the server stops between the two halves of a Save.
    desk.drafts.keep(default_layout)
    desk.restart()
    assert desk.drafts.current() is None
    assert desk.editors.enter(desk.open_editor().id)["situation"] == "editing"
