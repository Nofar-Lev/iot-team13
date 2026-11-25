// Shared by the desktop editor and the phone editor: leaving the editor through its own way
// out, the Home button.
//
// With nothing unsaved, the editor simply leaves. With unsaved changes it asks first: keep
// them as a draft, save them, discard them, or stay. The question is also the reminder for
// someone who forgot that something is unsaved.
//
// Closing the tab asks nothing: a browser gives a page no dialog of its own at that moment.
// The draft is on the server, so nothing is lost by it.

import { leavingQuestion } from "./session_messages.js";

/**
 * state, saving: the editor's state, and its Save and Discard (saving.js).
 * dialog:        where the question is shown (dialog.js).
 * goHome():      go to the home page. The session is told first (the editor's own function).
 * Returns the function to call when the user asks to leave.
 */
export function createLeaving({ state, saving, dialog, goHome }) {
  const question = leavingQuestion({
    keepAsDraft: goHome,
    async saveChanges() {
      if (await saving.save()) return goHome();
      // Not saved. If the question is still on the screen, take it away, so that the reason
      // can be read and the layout fixed. (A lost connection has put its own message there.)
      if (dialog.showing() === question.name) dialog.close();
    },
    async discardChanges() {
      if (await saving.discard()) goHome();
    },
    returnToTheEditor() {},
  });

  return function leave() {
    if (state.hasUnsavedChanges()) dialog.show(question);
    else goHome();
  };
}
