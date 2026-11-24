"""The rules of the display editor: one editor is in use at a time, and another can take over.

An "editor" here is one open editor page, known by the id of its live channel. It exists for
as long as that channel is connected; a page that reloads comes back as a new editor.

The rules, in short (docs/one-editor-at-a-time-plan.md has them in full):

- Unsaved work is the draft, kept by the server. Only the editor in use may change it, save it
  or discard it.
- A newly opened editor that finds nobody else simply starts, unless a draft was left behind:
  then it is asked whether to resume it or discard it.
- A newly opened editor that finds another one in use takes over at once when nothing is
  unsaved. When there is a draft, it chooses whether to continue it or discard it, and the
  other editor is asked to approve or refuse. No answer in time counts as approval.
- While a take-over waits for its answer, every other editor is told to try again later.

Every question an editor asks is answered with the situation it is in now: one of the names
below, with what goes with it. An editor whose situation changed between its question and its
choice is simply told the new situation.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any, Optional

from .draft_store import DraftStore
from .layout_store import LayoutStore, LayoutValidator
from .live_updates import EDITOR, LiveUpdates
from .timers import CancelTimer, RealTimers

# The situations an editor can be told it is in.
EDITING = "editing"                                         # it is the editor in use
DRAFT_LEFT_BEHIND = "draft_left_behind"                     # nobody is editing, and there is a draft
ANOTHER_EDITOR_HAS_UNSAVED_CHANGES = "another_editor_has_unsaved_changes"
WAITING_FOR_THE_OTHER_EDITOR = "waiting_for_the_other_editor"   # it asked to take over
TAKE_OVER_IN_PROGRESS = "take_over_in_progress"             # two other editors are in the middle of one

# What became of the old editor's unsaved changes when it was taken over.
CHANGES_CARRIED_OVER = "carried_over"
CHANGES_DISCARDED = "discarded"
NO_CHANGES = "none"

Situation = dict[str, Any]


class Refused(Exception):
    """The server will not do what an editor asked. `reason` is a short name a page can act on."""
    reason = "refused"
    message = "The server refused."


class EditorNotConnected(Refused):
    reason = "not_connected"
    message = "This editor has no live connection to the server."


class NotTheEditorInUse(Refused):
    reason = "not_the_editor_in_use"
    message = "This editor is not the one in use."


class NoTakeOverToAnswer(Refused):
    reason = "no_take_over_to_answer"
    message = "No other editor is waiting for this editor's answer."


class LayoutNotAccepted(Exception):
    """A layout that breaks the rules was sent as the draft. `problems` says what is wrong."""

    def __init__(self, problems: list):
        super().__init__("The layout breaks the rules.")
        self.problems = problems


@dataclass
class TakeOverWaiting:
    """A take-over that the editor in use has been asked about, and has not answered yet."""
    new_editor: str
    keep_changes: bool          # the new editor's choice: continue the draft, or discard it
    deadline: float             # on the timers' clock
    cancel_timer: CancelTimer


class OneEditorAtATime:
    def __init__(
        self,
        store: LayoutStore,
        drafts: DraftStore,
        live_updates: LiveUpdates,
        validator: LayoutValidator,
        take_over_seconds: float,
        timers: Any = None,
    ):
        self._store = store
        self._drafts = drafts
        self._live_updates = live_updates
        self._validator = validator
        self._take_over_seconds = take_over_seconds
        self._timers = timers or RealTimers()

        self._lock = threading.Lock()
        self._editor_in_use: Optional[str] = None
        self._take_over: Optional[TakeOverWaiting] = None

        # A draft equal to the saved layout holds nothing unsaved. One can be left on disk if
        # the server stopped between the two halves of a Save.
        if self._drafts.current() == self._store.current().layout:
            self._drafts.erase()

    # ---- Opening the editor -------------------------------------------------------------

    def enter(self, editor: str) -> Situation:
        """A newly opened editor asks to be the one in use."""
        with self._lock:
            self._must_be_connected(editor)
            return self._enter(editor)

    def answer_about_the_draft_left_behind(self, editor: str, keep_changes: bool) -> Situation:
        """An editor that found a draft and nobody editing chose to resume it or to discard it."""
        with self._lock:
            self._must_be_connected(editor)
            a_draft_is_still_left_behind = self._editor_in_use is None and self._drafts.current() is not None
            if not a_draft_is_still_left_behind:
                return self._enter(editor)
            if not keep_changes:
                self._drafts.erase()
            return self._start_editing(editor)

    def leave(self, editor: str) -> None:
        """An editor is gone: its page said so, or its live channel closed."""
        with self._lock:
            take_over = self._take_over
            if take_over is not None and take_over.new_editor == editor:
                # The editor that asked to take over is gone. The editor in use goes on.
                self._withdraw_take_over()
            elif editor == self._editor_in_use:
                if take_over is not None:
                    # Nobody is left to answer, so the editor that asked is not kept waiting.
                    self._complete_take_over()
                else:
                    self._editor_in_use = None   # the draft, if there is one, stays

    # ---- The editor in use: the draft, Save and Discard ---------------------------------

    def update_draft(self, editor: str, layout: Any) -> dict[str, Any]:
        """The editor in use changed something: this is the layout as it is now."""
        with self._lock:
            self._must_be_in_use(editor)
            problems = self._validator(layout)
            if problems:
                raise LayoutNotAccepted(problems)
            if layout == self._store.current().layout:
                self._drafts.erase()   # changed back to what is saved: nothing is unsaved
            else:
                self._drafts.keep(layout)
            return {"has_unsaved_changes": self._drafts.current() is not None}

    def save(self, editor: str) -> dict[str, Any]:
        """The draft becomes the saved layout, and every connected page is told."""
        with self._lock:
            self._must_be_in_use(editor)
            draft = self._drafts.current()
            if draft is None:
                saved = self._store.current()   # nothing is unsaved, so nothing changes
            else:
                saved = self._store.save(draft)
                self._drafts.erase()
                self._live_updates.announce("layout", {"revision": saved.revision, "saved_at": saved.saved_at})
            return {"revision": saved.revision, "saved_at": saved.saved_at}

    def discard(self, editor: str) -> Situation:
        """The draft is erased. The answer carries the saved layout, to go on editing from."""
        with self._lock:
            self._must_be_in_use(editor)
            self._drafts.erase()
            return self._editing()

    # ---- Taking over --------------------------------------------------------------------

    def ask_to_take_over(self, editor: str, keep_changes: bool) -> Situation:
        """An editor that found another one with unsaved changes chose to take over from it."""
        with self._lock:
            self._must_be_connected(editor)
            if editor == self._editor_in_use or self._take_over is not None:
                return self._enter(editor)
            if self._editor_in_use is None:
                # The other editor left in the meantime. The choice about its changes stands.
                if not keep_changes:
                    self._drafts.erase()
                return self._start_editing(editor)
            if self._drafts.current() is None:
                return self._enter(editor)   # nothing is unsaved any more: take over at once

            take_over = TakeOverWaiting(
                new_editor=editor,
                keep_changes=keep_changes,
                deadline=self._timers.now() + self._take_over_seconds,
                cancel_timer=lambda: None,
            )
            take_over.cancel_timer = self._timers.call_after(
                self._take_over_seconds, lambda: self._time_ran_out(take_over))
            self._take_over = take_over
            self._live_updates.tell(self._editor_in_use, "take_over_request", {
                "keep_changes": keep_changes,
                "seconds": self._take_over_seconds,
            })
            return self._waiting()

    def approve_take_over(self, editor: str) -> None:
        with self._lock:
            self._must_have_been_asked(editor)
            self._complete_take_over()

    def refuse_take_over(self, editor: str) -> None:
        with self._lock:
            self._must_have_been_asked(editor)
            new_editor = self._take_over.new_editor
            self._forget_take_over()
            self._live_updates.tell(new_editor, "take_over_refused", {})

    def _time_ran_out(self, take_over: TakeOverWaiting) -> None:
        with self._lock:
            # The timer may go off just after an answer arrived; then there is nothing to do.
            if self._take_over is take_over:
                self._complete_take_over()

    # ---- Helpers. They expect the caller to hold the lock. ------------------------------

    def _enter(self, editor: str) -> Situation:
        """The situation of an editor that wants to be the one in use, starting it if nothing is in the way."""
        if editor == self._editor_in_use:
            return self._editing()
        if self._take_over is not None:
            if self._take_over.new_editor == editor:
                return self._waiting()
            return {"situation": TAKE_OVER_IN_PROGRESS}

        something_is_unsaved = self._drafts.current() is not None
        if self._editor_in_use is None:
            if something_is_unsaved:
                return {"situation": DRAFT_LEFT_BEHIND}
            return self._start_editing(editor)
        if something_is_unsaved:
            return {"situation": ANOTHER_EDITOR_HAS_UNSAVED_CHANGES}

        # Another editor is in use, with nothing to lose: take over at once.
        self._live_updates.tell(self._editor_in_use, "taken_over", {"changes": NO_CHANGES})
        return self._start_editing(editor)

    def _start_editing(self, editor: str) -> Situation:
        self._editor_in_use = editor
        return self._editing()

    def _editing(self) -> Situation:
        """What the editor in use needs: the saved layout, and the draft if something is unsaved."""
        return {
            "situation": EDITING,
            "saved": self._store.current().as_json(),
            "draft": self._drafts.current(),
        }

    def _waiting(self) -> Situation:
        seconds_left = max(0.0, self._take_over.deadline - self._timers.now())
        return {"situation": WAITING_FOR_THE_OTHER_EDITOR, "seconds": seconds_left}

    def _complete_take_over(self) -> None:
        """The waiting take-over happens: approved, not answered in time, or nobody left to answer."""
        old_editor, take_over = self._editor_in_use, self._take_over
        self._forget_take_over()

        if self._drafts.current() is None:
            what_became_of_the_changes = NO_CHANGES   # saved or discarded while the question waited
        elif take_over.keep_changes:
            what_became_of_the_changes = CHANGES_CARRIED_OVER
        else:
            self._drafts.erase()
            what_became_of_the_changes = CHANGES_DISCARDED

        self._live_updates.tell(old_editor, "taken_over", {"changes": what_became_of_the_changes})
        self._live_updates.tell(take_over.new_editor, "take_over_granted", self._start_editing(take_over.new_editor))

    def _withdraw_take_over(self) -> None:
        self._forget_take_over()
        self._live_updates.tell(self._editor_in_use, "take_over_withdrawn", {})

    def _forget_take_over(self) -> None:
        self._take_over.cancel_timer()
        self._take_over = None

    def _must_be_connected(self, editor: str) -> None:
        if not self._live_updates.is_connected(editor, EDITOR):
            raise EditorNotConnected()

    def _must_be_in_use(self, editor: str) -> None:
        if editor != self._editor_in_use:
            raise NotTheEditorInUse()

    def _must_have_been_asked(self, editor: str) -> None:
        if self._take_over is None or editor != self._editor_in_use:
            raise NoTakeOverToAnswer()
