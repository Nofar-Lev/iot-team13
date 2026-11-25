// Shared by the desktop editor and the phone editor: Save and Discard.
//
// Both go through the editing session, because the server keeps the unsaved work as a draft:
// Save makes the draft the saved layout, and Discard erases it. This file adds what the user
// sees: the editor's state is brought in line, and a short message says what happened.
//
// A lost connection is not reported here. The session tells the page about it as a
// situation, and the page shows that in a dialog.

import { showToast } from "../common/toast.js";

/**
 * isDisplayOnline(): whether a display is connected right now, for the message after a Save.
 * Returns { save(), discard(), isBusy() }.
 */
export function createSaving({ state, session, isDisplayOnline }) {
  let isBusy = false;

  /** Do one thing at a time. While it runs, another Save or Discard answers false. */
  async function oneAtATime(work) {
    if (isBusy) return false;
    isBusy = true;
    try {
      return await work();
    } finally {
      isBusy = false;
    }
  }

  return {
    /** Resolves to true when the layout is saved: it was saved now, or nothing was unsaved. */
    save: () => oneAtATime(async () => {
      if (!state.hasUnsavedChanges()) return true;
      const answer = await session.save();
      if (answer.saved) {
        state.markSaved();
        showToast(
          isDisplayOnline()
            ? "Saved. The display is updating."
            : "Saved. The display is offline and will update when it reconnects.",
          "success",
        );
        return true;
      }
      if (answer.problems.length > 0) {
        showToast(`The server refused the layout: ${answer.problems.join(" ")}`, "problem");
      }
      return false;
    }),

    /** Resolves to true when the changes are gone and the editor shows the saved layout. */
    discard: () => oneAtATime(async () => {
      if (!state.hasUnsavedChanges()) return true;
      if (!(await session.discard())) return false;
      state.discardChanges();
      return true;
    }),

    isBusy: () => isBusy,
  };
}
