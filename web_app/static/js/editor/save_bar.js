// The top bar's Save and Discard buttons, and the mark that says there are unsaved changes.

import { askForSecondClick } from "../common/second_click.js";
import { saveLayout } from "../common/server_api.js";
import { showToast } from "../common/toast.js";

/**
 * isDisplayOnline(): whether a display is connected right now, for the message after a Save.
 */
export function setUpSaveBar({ saveButton, discardButton, unsavedMark }, state, { isDisplayOnline }) {
  let isSaving = false;

  function refresh() {
    const hasChanges = state.hasUnsavedChanges();
    saveButton.disabled = !hasChanges || isSaving;
    discardButton.disabled = !hasChanges || isSaving;
    unsavedMark.hidden = !hasChanges;
  }

  async function save() {
    if (isSaving || !state.hasUnsavedChanges()) return;
    isSaving = true;
    refresh();
    try {
      const answer = await saveLayout(state.layout());
      if (answer.saved) {
        state.markSaved();
        showToast(
          isDisplayOnline()
            ? "Saved. The display is updating."
            : "Saved. The display is offline and will update when it reconnects.",
          "success",
        );
      } else {
        showToast(`The server refused the layout: ${answer.problems.join(" ")}`, "problem");
      }
    } catch {
      showToast("Could not reach the server. Nothing was saved.", "problem");
    } finally {
      isSaving = false;
      refresh();
    }
  }

  saveButton.addEventListener("click", save);

  const discardQuestion = askForSecondClick({
    button: discardButton,
    labelElement: discardButton,
    usualText: "Discard changes",
    askingText: "Click again to discard",
    shouldAsk: () => true,
    onConfirmed: () => state.discardChanges(),
  });

  window.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s") {
      event.preventDefault();
      save();
    }
  });

  // Leaving the page with unsaved changes: let the browser ask first.
  window.addEventListener("beforeunload", (event) => {
    if (state.hasUnsavedChanges()) event.preventDefault();
  });

  state.subscribe((kindOfChange) => {
    if (kindOfChange === "saved") discardQuestion.reset();
    refresh();
  });
  refresh();
}
