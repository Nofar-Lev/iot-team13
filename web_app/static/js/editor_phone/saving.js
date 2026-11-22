// Saving the layout from the phone editor.

import { saveLayout } from "../common/server_api.js";
import { showToast } from "../common/toast.js";

/**
 * isDisplayOnline(): whether a display is connected right now, for the message after a Save.
 * Returns { save(), isSaving() }. save() answers true when the layout is saved: it was
 * saved now, or there was nothing to save.
 */
export function createSaving({ state, isDisplayOnline }) {
  let isSaving = false;

  async function save() {
    if (isSaving) return false;
    if (!state.hasUnsavedChanges()) return true;
    isSaving = true;
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
        return true;
      }
      showToast(`The server refused the layout: ${answer.problems.join(" ")}`, "problem");
      return false;
    } catch {
      showToast("Could not reach the server. Nothing was saved.", "problem");
      return false;
    } finally {
      isSaving = false;
    }
  }

  return { save, isSaving: () => isSaving };
}
