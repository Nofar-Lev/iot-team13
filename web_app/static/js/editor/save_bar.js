// The top bar's Save and Discard buttons, and the mark that says there are unsaved changes.

import { askForSecondClick } from "../common/second_click.js";

/**
 * saving:           the editor's Save and Discard (../editing/saving.js).
 * isDialogShowing(): whether a dialog covers the editor, so that Ctrl+S waits its turn.
 */
export function setUpSaveBar({ saveButton, discardButton, unsavedMark }, state, saving, { isDialogShowing }) {
  function refresh() {
    const hasChanges = state.hasUnsavedChanges();
    saveButton.disabled = !hasChanges || saving.isBusy();
    discardButton.disabled = !hasChanges || saving.isBusy();
    unsavedMark.hidden = !hasChanges;
  }

  /** Save or discard, with the buttons greyed out while the server is asked. */
  async function run(saveOrDiscard) {
    const whenDone = saveOrDiscard();
    refresh();
    await whenDone;
    refresh();
  }

  saveButton.addEventListener("click", () => run(saving.save));

  const discardQuestion = askForSecondClick({
    button: discardButton,
    labelElement: discardButton,
    usualText: "Discard changes",
    askingText: "Click again to discard",
    shouldAsk: () => true,
    onConfirmed: () => run(saving.discard),
  });

  window.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s") {
      event.preventDefault();
      if (!isDialogShowing()) run(saving.save);
    }
  });

  state.subscribe((kindOfChange) => {
    if (kindOfChange === "saved") discardQuestion.reset();
    refresh();
  });
  refresh();
}
