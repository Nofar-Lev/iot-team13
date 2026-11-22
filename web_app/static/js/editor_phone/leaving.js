// Leaving the editor while there are unsaved changes.
//
// A desktop browser can be told to ask "leave this page?" first. Phone browsers often do not
// ask. So the editor's own way out, the Home button, asks by itself with a dialog
// (unsaved_changes_dialog.js), and this file keeps the browser's question for every other way
// of leaving.

export function guardUnsavedChanges(state) {
  let isLeavingOnPurpose = false;

  window.addEventListener("beforeunload", (event) => {
    if (state.hasUnsavedChanges() && !isLeavingOnPurpose) event.preventDefault();
  });

  return {
    /** Go to another page of the app. The user has already agreed to lose what is unsaved. */
    leaveTo(address) {
      isLeavingOnPurpose = true;
      window.location.href = address;
    },
  };
}
