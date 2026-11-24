// Shared by the desktop editor and the phone editor: one page's part in "one editor at a
// time" (docs/one-editor-at-a-time-plan.md). The server keeps the rules; this file is how an
// editor page lives by them.
//
// What it does:
//   - opens the live channel, once, and learns this editor's id from it;
//   - asks to be the editor in use, and tells the page which situation it is in;
//   - sends every change of the layout to the server's draft;
//   - saves and discards;
//   - passes on the page's answers about taking over;
//   - notices a lost connection, after which nothing more can be done here but a reload;
//   - tells the server when the page goes away.
//
// No page elements here. Each editor shows the situations in its own way: it gets every
// situation through onSituation(situation), where situation.name is one of:
//
//   "editing"                             this is the editor in use. Comes with `saved`
//                                         ({ revision, saved_at, layout }) and `draft` (the
//                                         unsaved layout to continue from, or null)
//   "draft_left_behind"                   nobody is editing, and unsaved changes were left.
//                                         Answer with resumeDraftLeftBehind() or
//                                         discardDraftLeftBehind(), or leave
//   "another_editor_has_unsaved_changes"  answer with askToTakeOver({ keepChanges }), or leave
//   "waiting_for_the_other_editor"        it was asked to hand over. Comes with `seconds`
//   "take_over_refused"                   the other editor goes on editing. Only leaving is left
//   "take_over_in_progress"               two other editors are in the middle of a take-over.
//                                         Only leaving is left
//   "asked_to_hand_over"                  another editor wants to take over from this one.
//                                         Comes with `keepChanges` (will it continue this
//                                         editor's unsaved changes?) and `seconds`. Answer with
//                                         approveTakeOver() or refuseTakeOver()
//   "back_to_editing"                     the question above is gone: refused, or withdrawn
//   "taken_over"                          another editor is now the one in use. Comes with
//                                         `changes`: "carried_over", "discarded" or "none".
//                                         Only leaving is left
//   "connection_lost"                     only a reload is left

import { openLiveChannel } from "../common/live_channel.js";
import { createDraftSender } from "./draft_sender.js";
import { askEditingServer, tellServerThisEditorIsLeaving } from "./editing_addresses.js";

// News that every page gets. The session passes it on to the editor page.
const NEWS_FOR_EVERY_PAGE = ["hello", "display", "layout"];

// A refused draft update can overtake the news that says why ("another editor took over").
// So the session waits this long for that news before it calls the connection lost.
const WAIT_FOR_THE_REASON_MS = 1000;

/**
 * onSituation(situation): called every time the situation changes (the names are above).
 * onNews(name, details):  the live channel's news for every page: "hello", "display", "layout".
 *
 * The rest stands in for the browser and the server in the tests, and is left out by the pages.
 */
export function createEditingSession({
  onSituation,
  onNews = () => {},
  openChannel = openLiveChannel,
  ask = askEditingServer,
  tellServerOfLeaving = tellServerThisEditorIsLeaving,
  whenThePageGoesAway = (callback) => window.addEventListener("pagehide", callback),
  waitForTheReasonMs = WAIT_FOR_THE_REASON_MS,
}) {
  let channel = null;
  let editorId = null;
  let isEditorInUse = false;
  let isOver = false;        // nothing more happens here: lost, taken over, refused, or left
  let hasToldServerOfLeaving = false;

  const draftSender = createDraftSender({
    send: sendDraft,
    onCouldNotSend: (error) => {
      if (error.reason === "not_the_editor_in_use") {
        setTimeout(connectionLost, waitForTheReasonMs);
      } else {
        connectionLost();
      }
    },
  });

  // ---- How it ends ---------------------------------------------------------------------

  /** Nothing more happens in this session. */
  function end() {
    isOver = true;
    isEditorInUse = false;
    draftSender.stop();
    if (channel) channel.close();
  }

  function endWith(situation) {
    if (isOver) return;
    end();
    onSituation(situation);
  }

  const connectionLost = () => endWith({ name: "connection_lost" });

  // ---- Asking the server ---------------------------------------------------------------

  /**
   * Ask the server for one thing. Resolves to its answer, or to null when it did not do it.
   * A server that cannot be reached, or that no longer knows this editor, means the
   * connection is lost; refusals named in mayBeRefusedFor are left to the caller.
   */
  async function askServer(address, more = {}, { method = "POST", mayBeRefusedFor = [] } = {}) {
    if (isOver) return null;
    let result;
    try {
      result = await ask(address, editorId, more, method);
    } catch {
      connectionLost();
      return null;
    }
    if (result.ok) return result.answer;
    if (!mayBeRefusedFor.includes(result.reason)) connectionLost();
    return null;
  }

  /** Show the situation the server answered with: "editing", or one of the questions. */
  function showSituationFromServer(answer) {
    if (answer === null || isOver) return;
    const { situation: name, ...details } = answer;
    if (name === "editing") {
      isEditorInUse = true;
      draftSender.startFrom(details.draft ?? details.saved.layout);
      onSituation({ name, ...details });
    } else if (name === "take_over_in_progress") {
      endWith({ name });
    } else {
      onSituation({ name, ...details });
    }
  }

  // ---- The live channel ----------------------------------------------------------------

  function hearNews(name, details) {
    if (isOver) return;
    if (NEWS_FOR_EVERY_PAGE.includes(name)) onNews(name, details);

    if (name === "hello" && editorId === null) {
      editorId = details.editor;
      askServer("enter").then(showSituationFromServer);
    } else if (name === "take_over_request" && isEditorInUse) {
      onSituation({ name: "asked_to_hand_over", keepChanges: details.keep_changes, seconds: details.seconds });
    } else if (name === "take_over_withdrawn" && isEditorInUse) {
      onSituation({ name: "back_to_editing" });
    } else if (name === "taken_over") {
      endWith({ name: "taken_over", changes: details.changes });
    } else if (name === "take_over_refused") {
      endWith({ name: "take_over_refused" });
    } else if (name === "take_over_granted") {
      showSituationFromServer(details);
    }
  }

  // ---- The draft -----------------------------------------------------------------------

  async function sendDraft(layout) {
    const result = await ask("draft", editorId, { layout }, "PUT");
    if (result.ok) return { accepted: true };
    if (result.status === 400) return { accepted: false, problems: result.problems };
    throw Object.assign(new Error("The server refused the draft."), { reason: result.reason });
  }

  return {
    /** Open the live channel and ask to be the editor in use. Call once. */
    start() {
      channel = openChannel({
        role: "editor",
        tryAgainWhenLost: false,
        onNews: hearNews,
        onConnectionChange: (isConnected) => {
          if (!isConnected) connectionLost();
        },
      });
      whenThePageGoesAway(() => {
        if (editorId !== null && !hasToldServerOfLeaving) tellServerOfLeaving(editorId);
      });
    },

    // ---- Answers to the questions a newly opened editor is asked ----

    async resumeDraftLeftBehind() {
      showSituationFromServer(await askServer("draft-left-behind", { keep_changes: true }));
    },

    async discardDraftLeftBehind() {
      showSituationFromServer(await askServer("draft-left-behind", { keep_changes: false }));
    },

    /** keepChanges: continue the other editor's unsaved changes (true) or discard them (false). */
    async askToTakeOver({ keepChanges }) {
      showSituationFromServer(await askServer("take-over", { keep_changes: keepChanges }));
    },

    // ---- Answers of the editor in use, when another one asks to take over ----

    /** Hand over. "taken_over" follows. */
    async approveTakeOver() {
      // Too late or no longer asked: the news that says what happened is on its way.
      await askServer("take-over/approve", {}, { mayBeRefusedFor: ["no_take_over_to_answer"] });
    },

    /** Go on editing. "back_to_editing" follows. */
    async refuseTakeOver() {
      const answer = await askServer("take-over/refuse", {}, { mayBeRefusedFor: ["no_take_over_to_answer"] });
      if (answer !== null && !isOver) onSituation({ name: "back_to_editing" });
    },

    // ---- Editing ----

    /** The layout as it is now, after any change. It reaches the server's draft by itself. */
    layoutChanged(layout) {
      if (isEditorInUse) draftSender.layoutChanged(layout);
    },

    /**
     * Make the draft the saved layout.
     * Resolves to { saved: true, revision, saved_at }, or to { saved: false, problems }.
     * `problems` lists what the server found wrong with the layout; it is empty when the
     * reason is a lost connection, which the page is told about as a situation.
     */
    async save() {
      if (!isEditorInUse) return { saved: false, problems: [] };
      await draftSender.whenEverythingIsSent();
      if (draftSender.problems()) return { saved: false, problems: draftSender.problems() };
      const answer = await askServer("save");
      if (answer === null) return { saved: false, problems: [] };
      return { saved: true, revision: answer.revision, saved_at: answer.saved_at };
    },

    /**
     * Erase the draft. Resolves to true when the server did; the page then goes back to the
     * saved layout (editor_state.js: discardChanges).
     */
    async discard() {
      if (!isEditorInUse) return false;
      await draftSender.whenEverythingIsSent();
      const answer = await askServer("discard");
      if (answer === null) return false;
      draftSender.startFrom(answer.saved.layout);
      return true;
    },

    /**
     * Leave the editor on purpose, for example to go to the home page. Resolves once the
     * server knows, or cannot be told; then the page may go.
     */
    async leave() {
      if (editorId === null) return end();
      if (isEditorInUse) await draftSender.whenEverythingIsSent();
      end();
      hasToldServerOfLeaving = true;
      try {
        await ask("leave", editorId);
      } catch {
        // The server cannot be reached. It notices by itself that this editor is gone.
      }
    },
  };
}
