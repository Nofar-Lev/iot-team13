// Tests for what the messages of "one editor at a time" say, and what their buttons do.
// Run with:  node --test   (from the app's folder, web_app/iot-team-13)

import assert from "node:assert/strict";
import { test } from "node:test";

import { countdownStage, leavingQuestion, messageFor } from "../static/js/editing/session_messages.js";

/** Stand-ins for the session and the page, that write down what was asked of them. */
function newPage() {
  const done = [];
  const note = (what) => (...details) => done.push(details.length ? [what, ...details] : what);
  const actions = {
    session: {
      resumeDraftLeftBehind: note("resume"),
      discardDraftLeftBehind: note("discard the draft left behind"),
      askToTakeOver: note("ask to take over"),
      approveTakeOver: note("approve"),
      refuseTakeOver: note("refuse"),
    },
    goHome: note("go home"),
    reload: note("reload"),
  };
  return { done, actions };
}

const message = (situation) => messageFor(situation, newPage().actions);
const labels = (theMessage) => theMessage.buttons.map((button) => button.label);
const looks = (theMessage) => theMessage.buttons.map((button) => button.look);

/** Click the button with this name, and return what it asked for. */
function click(situation, buttonName) {
  const { done, actions } = newPage();
  messageFor(situation, actions).buttons.find((button) => button.name === buttonName).onClick();
  return done;
}

// --- No message --------------------------------------------------------------------------------

for (const name of ["editing", "back_to_editing"]) {
  test(`"${name}" needs no message: the editor is in use`, () => {
    assert.equal(message({ name, saved: {}, draft: null }), null);
  });
}

// --- A newly opened editor ---------------------------------------------------------------------

test("a draft that was left behind: resume, discard, or return to home", () => {
  const situation = { name: "draft_left_behind" };
  assert.equal(message(situation).title, "Unsaved changes were left here");
  assert.deepEqual(labels(message(situation)), ["Resume", "Discard", "Return to home"]);
  assert.deepEqual(looks(message(situation)), ["main", "discards", "plain"]);
  assert.deepEqual(click(situation, "resume"), ["resume"]);
  assert.deepEqual(click(situation, "discard"), ["discard the draft left behind"]);
  assert.deepEqual(click(situation, "return-to-home"), ["go home"]);
});

test("another editor has unsaved changes: take over and continue, take over and discard, or return to home", () => {
  const situation = { name: "another_editor_has_unsaved_changes" };
  assert.deepEqual(labels(message(situation)), [
    "Take over and continue its changes", "Take over and discard its changes", "Return to home",
  ]);
  assert.deepEqual(looks(message(situation)), ["main", "discards", "plain"]);
  assert.equal(message(situation).stacked, true);
  assert.deepEqual(click(situation, "take-over-and-continue"), [["ask to take over", { keepChanges: true }]]);
  assert.deepEqual(click(situation, "take-over-and-discard"), [["ask to take over", { keepChanges: false }]]);
  assert.deepEqual(click(situation, "return-to-home"), ["go home"]);
});

test("waiting for the other editor: a calm countdown, and a way home", () => {
  const waiting = message({ name: "waiting_for_the_other_editor", seconds: 20 });
  assert.equal(waiting.countdown.seconds, 20);
  assert.equal(waiting.countdown.warnsAsItRunsOut, false);
  assert.equal(waiting.countdown.label(14), "14 seconds left");
  assert.equal(waiting.countdown.label(1), "1 second left");
  assert.deepEqual(labels(waiting), ["Return to home"]);
});

for (const [name, title] of [
  ["take_over_refused", "The other editor is still in use"],
  ["take_over_in_progress", "Someone else is taking over the editor"],
]) {
  test(`"${name}" says so, and only offers the way home`, () => {
    assert.equal(message({ name }).title, title);
    assert.deepEqual(labels(message({ name })), ["Return to home"]);
    assert.deepEqual(click({ name }, "return-to-home"), ["go home"]);
  });
}

// --- The editor in use, asked to hand over -----------------------------------------------------

test("asked to hand over to an editor that continues the changes: approving loses nothing", () => {
  const situation = { name: "asked_to_hand_over", keepChanges: true, seconds: 20 };
  assert.equal(message(situation).title, "Another editor wants to take over");
  assert.equal(message(situation).text, "It will continue from your unsaved changes. Nothing is lost.");
  assert.deepEqual(labels(message(situation)), ["Approve", "Refuse"]);
  assert.deepEqual(looks(message(situation)), ["main", "plain"]);
  assert.deepEqual(click(situation, "approve"), ["approve"]);
  assert.deepEqual(click(situation, "refuse"), ["refuse"]);
});

test("asked to hand over to an editor that discards the changes: approving is marked as throwing work away", () => {
  const situation = { name: "asked_to_hand_over", keepChanges: false, seconds: 20 };
  assert.equal(message(situation).text, "Your unsaved changes will be discarded.");
  assert.deepEqual(looks(message(situation)), ["discards", "plain"]);
});

test("the countdown of the editor that is asked warns as it runs out", () => {
  const { countdown } = message({ name: "asked_to_hand_over", keepChanges: true, seconds: 20 });
  assert.equal(countdown.warnsAsItRunsOut, true);
  assert.equal(countdown.label(14), "If you do not answer, it takes over in 14 seconds");
  assert.equal(countdown.label(1), "If you do not answer, it takes over in 1 second");
});

for (const [changes, text] of [
  ["carried_over", "Your unsaved changes were carried over to it."],
  ["discarded", "Your unsaved changes were discarded."],
  ["none", "You had no unsaved changes."],
]) {
  test(`taken over, changes "${changes}": the message says what became of them`, () => {
    const takenOver = message({ name: "taken_over", changes });
    assert.equal(takenOver.title, "Another editor is now in use");
    assert.equal(takenOver.text, text);
    assert.deepEqual(labels(takenOver), ["Return to home"]);
  });
}

test("a lost connection only offers a reload", () => {
  const situation = { name: "connection_lost" };
  assert.equal(message(situation).title, "The connection was lost");
  assert.deepEqual(labels(message(situation)), ["Reload"]);
  assert.deepEqual(click(situation, "reload"), ["reload"]);
});

test("only the question on leaving can be dismissed", () => {
  for (const situation of [
    { name: "draft_left_behind" }, { name: "another_editor_has_unsaved_changes" },
    { name: "waiting_for_the_other_editor", seconds: 20 }, { name: "take_over_refused" },
    { name: "take_over_in_progress" }, { name: "asked_to_hand_over", keepChanges: true, seconds: 20 },
    { name: "taken_over", changes: "none" }, { name: "connection_lost" },
  ]) {
    assert.equal(message(situation).dismiss ?? null, null, situation.name);
  }
});

// --- The timer's colours -----------------------------------------------------------------------

test("a countdown is calm, then warns at half the time, then at the last quarter", () => {
  assert.equal(countdownStage(1), "calm");
  assert.equal(countdownStage(0.51), "calm");
  assert.equal(countdownStage(0.5), "soon");
  assert.equal(countdownStage(0.26), "soon");
  assert.equal(countdownStage(0.25), "now");
  assert.equal(countdownStage(0), "now");
});

// --- Leaving with unsaved changes --------------------------------------------------------------

test("the question on leaving: three explained ways to leave, and a quiet way to stay", () => {
  const done = [];
  const question = leavingQuestion({
    keepAsDraft: () => done.push("keep as draft"),
    saveChanges: () => done.push("save changes"),
    discardChanges: () => done.push("discard changes"),
    returnToTheEditor: () => done.push("return to the editor"),
  });

  assert.equal(question.title, "You have unsaved changes");
  assert.deepEqual(labels(question), ["Keep as draft", "Save changes", "Discard changes"]);
  assert.deepEqual(looks(question), ["main", "soft", "discards"]);
  assert.deepEqual(question.buttons.map((button) => button.explanation), [
    "Finish later. The display stays as it is.",
    "The display shows them now.",
    "Your changes are erased.",
  ]);
  assert.equal(question.dismiss.label, "Return to the editor");

  for (const button of question.buttons) button.onClick();
  question.dismiss.onClick();
  assert.deepEqual(done, ["keep as draft", "save changes", "discard changes", "return to the editor"]);
});
