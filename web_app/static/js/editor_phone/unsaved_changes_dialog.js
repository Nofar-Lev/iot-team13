// The question asked when the user leaves the editor with unsaved changes:
//
//     Save   /   Discard   /   Return to the editor
//
// It is a dialog over the editing screen, the way a word processor asks when a document with
// unsaved changes is closed. A phone's browser often does not ask by itself, and a button
// that only said "tap again" would not say what happens to the changes.

import { el } from "../common/dom.js";

// The three answers.
export const SAVE = "save";
export const DISCARD = "discard";
export const RETURN_TO_THE_EDITOR = "return";

function choiceButton(className, id, text) {
  const button = el("button", `dialog__button ${className}`, text);
  button.type = "button";
  button.id = id;
  return button;
}

/**
 * holder: the element the dialog covers (the editing screen).
 * Returns { ask() }. ask() shows the dialog and answers, once the user has chosen, with
 * SAVE, DISCARD or RETURN_TO_THE_EDITOR. A tap beside the dialog means "return".
 */
export function createUnsavedChangesDialog(holder) {
  const title = el("h2", "dialog__title", "Unsaved changes");
  title.id = "unsaved-changes-title";
  const text = el("p", "dialog__text", "The layout has changes that were not saved. What should happen to them?");

  const saveButton = choiceButton("dialog__button--save", "leave-and-save-button", "Save");
  const discardButton = choiceButton("dialog__button--discard", "leave-and-discard-button", "Discard");
  const returnButton = choiceButton("dialog__button--return", "return-to-editor-button", "Return to the editor");
  const buttons = el("div", "dialog__buttons");
  buttons.append(saveButton, discardButton, returnButton);

  const dialog = el("div", "dialog");
  dialog.setAttribute("role", "dialog");
  dialog.setAttribute("aria-modal", "true");
  dialog.setAttribute("aria-labelledby", title.id);
  dialog.append(title, text, buttons);

  const backdrop = el("div", "dialog-backdrop");
  backdrop.id = "unsaved-changes-dialog";
  backdrop.hidden = true;
  backdrop.append(dialog);
  holder.append(backdrop);

  let answerWith = null;   // the function that ends the question in progress, or null

  function answer(choice) {
    if (!answerWith) return;
    backdrop.hidden = true;
    const finish = answerWith;
    answerWith = null;
    finish(choice);
  }

  saveButton.addEventListener("click", () => answer(SAVE));
  discardButton.addEventListener("click", () => answer(DISCARD));
  returnButton.addEventListener("click", () => answer(RETURN_TO_THE_EDITOR));
  // Beside the dialog: the choice that loses nothing.
  backdrop.addEventListener("click", (event) => {
    if (event.target === backdrop) answer(RETURN_TO_THE_EDITOR);
  });

  return {
    ask() {
      // Asked again while already asking: the first question is answered "return".
      answer(RETURN_TO_THE_EDITOR);
      backdrop.hidden = false;
      return new Promise((resolve) => {
        answerWith = resolve;
      });
    },
  };
}
