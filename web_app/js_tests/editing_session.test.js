// Tests for an editor page's part in "one editor at a time": the editing session.
// Run with:  node --test   (from the web_app folder)
//
// The server and the live channel are replaced by stand-ins. A test decides what the server
// answers, sends news down the channel, and looks at what the page was told and what the
// server was asked. Nothing here uses the network or a browser.

import assert from "node:assert/strict";
import { test } from "node:test";

import { createEditingSession } from "../static/js/editing/editing_session.js";

const layoutWith = (marker) => ({ version: 1, screens: [{ background: marker, widgets: [] }] });
const SAVED = { revision: 4, saved_at: "2026-01-01T10:00:00+00:00", layout: layoutWith("saved") };
const EDITING = { situation: "editing", saved: SAVED, draft: null };
const EDITING_A_DRAFT = { situation: "editing", saved: SAVED, draft: layoutWith("draft") };

const did = (answer = {}) => ({ ok: true, answer });
const refused = (status, reason) => ({ ok: false, status, reason, problems: ["The server refused."] });
const aMoment = (milliseconds = 0) => new Promise((resolve) => setTimeout(resolve, milliseconds));

// How long the session waits, in these tests, for the news that explains a refused draft.
const WAIT_FOR_THE_REASON_MS = 20;

/**
 * A session with a stand-in server and channel around it.
 * `answers` says what the server answers at each address; the rest is answered with "done".
 */
function newWorld(answers = {}) {
  const world = {
    situations: [],        // every situation the page was told, oldest first
    news: [],              // the news that was passed on to the page
    asked: [],             // everything the server was asked: { address, editorId, more, method }
    toldOfLeaving: [],     // the last messages of a closing page
    channel: null,         // how the channel was opened
    isChannelClosed: false,
    isServerReachable: true,
    answers: { enter: did(EDITING), ...answers },
  };
  let pageGoesAway = () => {};

  world.session = createEditingSession({
    onSituation: (situation) => world.situations.push(situation),
    onNews: (name, details) => world.news.push(name),
    openChannel: (options) => {
      world.channel = options;
      return { close: () => { world.isChannelClosed = true; } };
    },
    ask: async (address, editorId, more = {}, method = "POST") => {
      world.asked.push({ address, editorId, more, method });
      if (!world.isServerReachable) throw new TypeError("fetch failed");
      const answer = world.answers[address] ?? did();
      return typeof answer === "function" ? answer() : answer;
    },
    tellServerOfLeaving: (editorId) => world.toldOfLeaving.push(editorId),
    whenThePageGoesAway: (callback) => { pageGoesAway = callback; },
    waitForTheReasonMs: WAIT_FOR_THE_REASON_MS,
  });

  world.hear = async (name, details = {}) => {
    world.channel.onNews(name, details);
    await aMoment();
  };
  /** The channel connects, the server gives this editor its id, and the editor enters. */
  world.connect = () => world.hear("hello", { revision: 4, saved_at: SAVED.saved_at, display_online: true, editor: "editor-1" });
  world.channelIsLost = async () => {
    world.channel.onConnectionChange(false);
    await aMoment();
  };
  world.pageGoesAway = () => pageGoesAway();
  world.addressesAsked = () => world.asked.map((request) => request.address);
  world.lastSituation = () => world.situations.at(-1);
  return world;
}

/** A world whose editor has entered and is the editor in use. */
async function worldWithEditorInUse(answers = {}) {
  const world = newWorld(answers);
  world.session.start();
  await world.connect();
  return world;
}

// --- Starting --------------------------------------------------------------------------------

test("starting opens the live channel as an editor, once, without trying again when it is lost", () => {
  const world = newWorld();
  world.session.start();
  assert.equal(world.channel.role, "editor");
  assert.equal(world.channel.tryAgainWhenLost, false);
  assert.deepEqual(world.asked, []);   // nothing is asked before the server has given an id
});

test("the editor enters with the id the server gave it, and the page is told it is editing", async () => {
  const world = await worldWithEditorInUse();
  assert.deepEqual(world.asked, [{ address: "enter", editorId: "editor-1", more: {}, method: "POST" }]);
  assert.deepEqual(world.situations, [{ name: "editing", saved: SAVED, draft: null }]);
});

test("the news that every page gets is passed on to the editor page, and the rest is not", async () => {
  const world = await worldWithEditorInUse();
  await world.hear("display", { online: false });
  await world.hear("layout", { revision: 5, saved_at: "later" });
  await world.hear("take_over_withdrawn");
  assert.deepEqual(world.news, ["hello", "display", "layout"]);
});

for (const situation of ["draft_left_behind", "another_editor_has_unsaved_changes"]) {
  test(`an editor that meets "${situation}" on entering is told so, and is not yet editing`, async () => {
    const world = await worldWithEditorInUse({ enter: did({ situation }) });
    assert.deepEqual(world.situations, [{ name: situation }]);
    world.session.layoutChanged(layoutWith("a change"));
    assert.deepEqual(world.addressesAsked(), ["enter"]);   // nothing is sent to the draft
    assert.equal(world.isChannelClosed, false);
  });
}

test("an editor that meets a take-over in progress is told so, and that is the end of it", async () => {
  const world = await worldWithEditorInUse({ enter: did({ situation: "take_over_in_progress" }) });
  assert.deepEqual(world.situations, [{ name: "take_over_in_progress" }]);
  assert.equal(world.isChannelClosed, true);
});

test("an editor the server does not know cannot go on: the connection counts as lost", async () => {
  const world = await worldWithEditorInUse({ enter: refused(409, "not_connected") });
  assert.deepEqual(world.situations, [{ name: "connection_lost" }]);
});

// --- A draft that was left behind --------------------------------------------------------------

test("resuming a draft that was left behind continues from it", async () => {
  const world = await worldWithEditorInUse({
    enter: did({ situation: "draft_left_behind" }),
    "draft-left-behind": did(EDITING_A_DRAFT),
  });
  await world.session.resumeDraftLeftBehind();
  assert.deepEqual(world.asked.at(-1).more, { keep_changes: true });
  assert.deepEqual(world.lastSituation(), { name: "editing", saved: SAVED, draft: layoutWith("draft") });

  world.session.layoutChanged(layoutWith("draft"));   // the page shows the draft: nothing new to send
  assert.equal(world.asked.at(-1).address, "draft-left-behind");
  world.session.layoutChanged(layoutWith("draft, and more"));
  assert.equal(world.asked.at(-1).address, "draft");
});

test("discarding a draft that was left behind starts from the saved layout", async () => {
  const world = await worldWithEditorInUse({
    enter: did({ situation: "draft_left_behind" }),
    "draft-left-behind": did(EDITING),
  });
  await world.session.discardDraftLeftBehind();
  assert.deepEqual(world.asked.at(-1).more, { keep_changes: false });
  assert.deepEqual(world.lastSituation(), { name: "editing", saved: SAVED, draft: null });
});

test("an editor that chose too late is told the situation as it is by then", async () => {
  const world = await worldWithEditorInUse({
    enter: did({ situation: "draft_left_behind" }),
    "draft-left-behind": did({ situation: "another_editor_has_unsaved_changes" }),
  });
  await world.session.resumeDraftLeftBehind();
  assert.deepEqual(world.lastSituation(), { name: "another_editor_has_unsaved_changes" });
});

// --- Taking over, as the new editor ------------------------------------------------------------

for (const keepChanges of [true, false]) {
  test(`asking to take over (keep the changes: ${keepChanges}) shows the wait and its seconds`, async () => {
    const world = await worldWithEditorInUse({
      enter: did({ situation: "another_editor_has_unsaved_changes" }),
      "take-over": did({ situation: "waiting_for_the_other_editor", seconds: 20 }),
    });
    await world.session.askToTakeOver({ keepChanges });
    assert.deepEqual(world.asked.at(-1), {
      address: "take-over", editorId: "editor-1", more: { keep_changes: keepChanges }, method: "POST",
    });
    assert.deepEqual(world.lastSituation(), { name: "waiting_for_the_other_editor", seconds: 20 });
  });
}

async function worldWaitingToTakeOver() {
  const world = await worldWithEditorInUse({
    enter: did({ situation: "another_editor_has_unsaved_changes" }),
    "take-over": did({ situation: "waiting_for_the_other_editor", seconds: 20 }),
  });
  await world.session.askToTakeOver({ keepChanges: true });
  return world;
}

test("a granted take-over makes this the editor in use, continuing the draft", async () => {
  const world = await worldWaitingToTakeOver();
  await world.hear("take_over_granted", EDITING_A_DRAFT);
  assert.deepEqual(world.lastSituation(), { name: "editing", saved: SAVED, draft: layoutWith("draft") });

  world.session.layoutChanged(layoutWith("draft, and more"));
  assert.equal(world.asked.at(-1).address, "draft");
});

test("a take-over that happens at once needs no waiting", async () => {
  const world = await worldWithEditorInUse({
    enter: did({ situation: "another_editor_has_unsaved_changes" }),
    "take-over": did(EDITING),   // the other editor saved or left in the meantime
  });
  await world.session.askToTakeOver({ keepChanges: false });
  assert.equal(world.lastSituation().name, "editing");
});

test("a refused take-over is the end of this session", async () => {
  const world = await worldWaitingToTakeOver();
  await world.hear("take_over_refused");
  assert.deepEqual(world.lastSituation(), { name: "take_over_refused" });
  assert.equal(world.isChannelClosed, true);

  const askedBefore = world.asked.length;
  await world.session.askToTakeOver({ keepChanges: true });
  await world.hear("take_over_granted", EDITING);
  assert.equal(world.asked.length, askedBefore);
  assert.deepEqual(world.lastSituation(), { name: "take_over_refused" });
});

// --- Taking over, as the old editor ------------------------------------------------------------

test("the editor in use is told when another editor asks to take over", async () => {
  const world = await worldWithEditorInUse();
  await world.hear("take_over_request", { keep_changes: false, seconds: 20 });
  assert.deepEqual(world.lastSituation(), { name: "asked_to_hand_over", keepChanges: false, seconds: 20 });
});

test("approving hands over: the server is told, and the news that follows ends the session", async () => {
  const world = await worldWithEditorInUse();
  await world.hear("take_over_request", { keep_changes: true, seconds: 20 });
  await world.session.approveTakeOver();
  assert.equal(world.asked.at(-1).address, "take-over/approve");

  await world.hear("taken_over", { changes: "carried_over" });
  assert.deepEqual(world.lastSituation(), { name: "taken_over", changes: "carried_over" });
  assert.equal(world.isChannelClosed, true);

  world.session.layoutChanged(layoutWith("too late"));
  assert.equal(world.asked.at(-1).address, "take-over/approve");   // nothing more is sent
});

test("with no answer, the news that the time ran out ends the session the same way", async () => {
  const world = await worldWithEditorInUse();
  await world.hear("take_over_request", { keep_changes: false, seconds: 20 });
  await world.hear("taken_over", { changes: "discarded" });
  assert.deepEqual(world.lastSituation(), { name: "taken_over", changes: "discarded" });
});

test("refusing goes back to editing", async () => {
  const world = await worldWithEditorInUse();
  await world.hear("take_over_request", { keep_changes: false, seconds: 20 });
  await world.session.refuseTakeOver();
  assert.equal(world.asked.at(-1).address, "take-over/refuse");
  assert.deepEqual(world.lastSituation(), { name: "back_to_editing" });

  world.session.layoutChanged(layoutWith("still editing"));
  assert.equal(world.asked.at(-1).address, "draft");
});

for (const answer of ["approveTakeOver", "refuseTakeOver"]) {
  test(`${answer} that comes too late changes nothing: the news says what happened`, async () => {
    const world = await worldWithEditorInUse({
      "take-over/approve": refused(409, "no_take_over_to_answer"),
      "take-over/refuse": refused(409, "no_take_over_to_answer"),
    });
    await world.hear("take_over_request", { keep_changes: false, seconds: 20 });
    await world.session[answer]();
    assert.equal(world.lastSituation().name, "asked_to_hand_over");   // not "connection_lost"
    await world.hear("taken_over", { changes: "discarded" });
    assert.deepEqual(world.lastSituation(), { name: "taken_over", changes: "discarded" });
  });
}

test("when the other editor stops asking, the question goes away", async () => {
  const world = await worldWithEditorInUse();
  await world.hear("take_over_request", { keep_changes: false, seconds: 20 });
  await world.hear("take_over_withdrawn");
  assert.deepEqual(world.lastSituation(), { name: "back_to_editing" });
});

test("being taken over at once, with nothing unsaved, ends the session", async () => {
  const world = await worldWithEditorInUse();
  await world.hear("taken_over", { changes: "none" });
  assert.deepEqual(world.lastSituation(), { name: "taken_over", changes: "none" });
});

// --- The draft ---------------------------------------------------------------------------------

test("a change of the layout is sent to the server's draft", async () => {
  const world = await worldWithEditorInUse();
  world.session.layoutChanged(layoutWith("a change"));
  assert.deepEqual(world.asked.at(-1), {
    address: "draft", editorId: "editor-1", more: { layout: layoutWith("a change") }, method: "PUT",
  });
});

test("a layout that is what the editor started from is not sent", async () => {
  const world = await worldWithEditorInUse();
  world.session.layoutChanged(layoutWith("saved"));
  assert.deepEqual(world.addressesAsked(), ["enter"]);
});

test("a change that cannot reach the server means the connection is lost", async () => {
  const world = await worldWithEditorInUse();
  world.isServerReachable = false;
  world.session.layoutChanged(layoutWith("a change"));
  await aMoment();
  assert.deepEqual(world.lastSituation(), { name: "connection_lost" });
  assert.equal(world.isChannelClosed, true);
});

test("a change refused because another editor took over waits for the news that says so", async () => {
  const world = await worldWithEditorInUse({ draft: refused(409, "not_the_editor_in_use") });
  world.session.layoutChanged(layoutWith("a change"));
  await aMoment();
  await world.hear("taken_over", { changes: "none" });   // the news arrives a little after the refusal
  await aMoment(2 * WAIT_FOR_THE_REASON_MS);
  assert.deepEqual(world.situations.map((situation) => situation.name), ["editing", "taken_over"]);
});

test("a change refused with no news to explain it means the connection was lost", async () => {
  // This is the editor that slept, was taken over, and woke up.
  const world = await worldWithEditorInUse({ draft: refused(409, "not_the_editor_in_use") });
  world.session.layoutChanged(layoutWith("a change"));
  await aMoment(2 * WAIT_FOR_THE_REASON_MS);
  assert.deepEqual(world.situations.map((situation) => situation.name), ["editing", "connection_lost"]);
});

// --- Save and Discard --------------------------------------------------------------------------

test("saving first lets the last change arrive, and then asks the server to save", async () => {
  const world = await worldWithEditorInUse({ save: did({ revision: 5, saved_at: "now" }) });
  world.session.layoutChanged(layoutWith("a change"));
  const answer = await world.session.save();
  assert.deepEqual(world.addressesAsked(), ["enter", "draft", "save"]);
  assert.deepEqual(answer, { saved: true, revision: 5, saved_at: "now" });
});

test("a layout the server finds faulty is not saved, and the page is told what is wrong", async () => {
  const world = await worldWithEditorInUse({
    draft: { ok: false, status: 400, reason: null, problems: ["A widget is outside the grid."] },
  });
  world.session.layoutChanged(layoutWith("faulty"));
  const answer = await world.session.save();
  assert.deepEqual(answer, { saved: false, problems: ["A widget is outside the grid."] });
  assert.deepEqual(world.addressesAsked(), ["enter", "draft"]);   // Save was not asked for
  assert.equal(world.lastSituation().name, "editing");            // and the editor goes on
});

test("a save that cannot reach the server saves nothing and means the connection is lost", async () => {
  const world = await worldWithEditorInUse();
  world.isServerReachable = false;
  assert.deepEqual(await world.session.save(), { saved: false, problems: [] });
  assert.deepEqual(world.lastSituation(), { name: "connection_lost" });
});

test("discarding asks the server to erase the draft, after the last change arrived", async () => {
  const world = await worldWithEditorInUse({ discard: did(EDITING) });
  world.session.layoutChanged(layoutWith("a change"));
  assert.equal(await world.session.discard(), true);
  assert.deepEqual(world.addressesAsked(), ["enter", "draft", "discard"]);

  world.session.layoutChanged(layoutWith("saved"));   // the page went back to the saved layout
  assert.deepEqual(world.addressesAsked(), ["enter", "draft", "discard"]);
  assert.equal(world.situations.length, 1);           // the page is not told "editing" again
});

test("a discard that cannot reach the server answers false", async () => {
  const world = await worldWithEditorInUse();
  world.isServerReachable = false;
  assert.equal(await world.session.discard(), false);
  assert.deepEqual(world.lastSituation(), { name: "connection_lost" });
});

test("an editor that is not the one in use saves and discards nothing", async () => {
  const world = await worldWithEditorInUse({ enter: did({ situation: "draft_left_behind" }) });
  assert.deepEqual(await world.session.save(), { saved: false, problems: [] });
  assert.equal(await world.session.discard(), false);
  assert.deepEqual(world.addressesAsked(), ["enter"]);
});

// --- A lost connection -------------------------------------------------------------------------

test("a lost live channel is told to the page once, and nothing can be done after it", async () => {
  const world = await worldWithEditorInUse();
  await world.channelIsLost();
  await world.channelIsLost();
  assert.deepEqual(world.situations.map((situation) => situation.name), ["editing", "connection_lost"]);
  assert.equal(world.isChannelClosed, true);

  world.session.layoutChanged(layoutWith("a change"));
  await world.session.save();
  await world.session.discard();
  await world.session.refuseTakeOver();
  await world.hear("take_over_request", { keep_changes: true, seconds: 20 });
  assert.deepEqual(world.addressesAsked(), ["enter"]);
  assert.equal(world.lastSituation().name, "connection_lost");
});

test("a channel that never connects counts as a lost connection", async () => {
  const world = newWorld();
  world.session.start();
  await world.channelIsLost();
  assert.deepEqual(world.situations, [{ name: "connection_lost" }]);
  assert.deepEqual(world.asked, []);
});

test("a connection lost while a question is on the screen replaces the question", async () => {
  const world = await worldWaitingToTakeOver();
  await world.channelIsLost();
  assert.deepEqual(world.lastSituation(), { name: "connection_lost" });
});

test("after being taken over, a closing channel is not reported as a lost connection", async () => {
  const world = await worldWithEditorInUse();
  await world.hear("taken_over", { changes: "none" });
  await world.channelIsLost();
  assert.deepEqual(world.lastSituation(), { name: "taken_over", changes: "none" });
});

// --- Leaving -----------------------------------------------------------------------------------

test("leaving on purpose lets the last change arrive, tells the server, and closes the channel", async () => {
  const world = await worldWithEditorInUse();
  world.session.layoutChanged(layoutWith("a change"));
  await world.session.leave();
  assert.deepEqual(world.addressesAsked(), ["enter", "draft", "leave"]);
  assert.equal(world.asked.at(-1).editorId, "editor-1");
  assert.equal(world.isChannelClosed, true);
  assert.equal(world.situations.length, 1);   // leaving is not a situation: the page is going

  world.pageGoesAway();
  assert.deepEqual(world.toldOfLeaving, []);   // the server was told already
});

test("leaving while the server cannot be reached still lets the page go", async () => {
  const world = await worldWithEditorInUse();
  world.isServerReachable = false;
  await world.session.leave();
  assert.equal(world.isChannelClosed, true);
});

test("leaving while waiting to take over tells the server, which stops the asking", async () => {
  const world = await worldWaitingToTakeOver();
  await world.session.leave();
  assert.equal(world.asked.at(-1).address, "leave");
});

test("a page that goes away by itself sends a last message with its id", async () => {
  const world = await worldWithEditorInUse();
  world.pageGoesAway();
  assert.deepEqual(world.toldOfLeaving, ["editor-1"]);
});

test("a page that goes away after its connection was lost still says so, for when it returns", async () => {
  const world = await worldWithEditorInUse();
  await world.channelIsLost();
  world.pageGoesAway();
  assert.deepEqual(world.toldOfLeaving, ["editor-1"]);
});

test("a page that goes away before it was given an id has nothing to say", () => {
  const world = newWorld();
  world.session.start();
  world.pageGoesAway();
  assert.deepEqual(world.toldOfLeaving, []);
});
