// The start screen: one button that opens the editing screen in full screen.
//
// A page may only go full screen after a tap, so the editor cannot open that way by itself.
// Leaving full screen brings the start screen back. The layout being edited is not touched by
// any of this: unsaved changes are still there when the editing screen is opened again.
//
// The button is shown only once the editor is ready: its code has arrived (or this file
// would not be running), the layout has arrived, the preview is drawn and the background
// pictures are there. Until then the start screen shows "Loading editor...", which is how the
// page itself starts out (editor_phone.html). So a tap always lands on a button that works,
// and opens the editor at once.

import { enterFullScreenSideways, onLeavingFullScreen } from "./full_screen_sideways.js";

/**
 * startScreen, editingScreen: the two elements, of which one shows at a time.
 * openButton:                 the button on the start screen.
 * whenEditorIsReady:          a promise that gives true once the editing screen can be shown,
 *                             or false if the editor could not load.
 */
export function setUpStartScreen({ startScreen, editingScreen, openButton, whenEditorIsReady }) {
  let openedInFullScreen = false;
  let isOpening = false;

  function showEditingScreen() {
    startScreen.hidden = true;
    editingScreen.hidden = false;
    document.body.dataset.showing = "editing";
  }

  /** state: "loading", "ready", "opening" or "failed" (see editor_phone.html). */
  function showStartScreen(state) {
    startScreen.dataset.state = state;
    editingScreen.hidden = true;
    startScreen.hidden = false;
    document.body.dataset.showing = "start";
  }

  openButton.addEventListener("click", async () => {
    if (isOpening) return;   // a second tap while the browser is still switching to full screen
    isOpening = true;
    showStartScreen("opening");
    openedInFullScreen = await enterFullScreenSideways();
    isOpening = false;
    showEditingScreen();
  });

  // Only a page that was in full screen goes back to the start screen when full screen ends.
  // Where full screen never happened, there is nothing to leave.
  onLeavingFullScreen(() => {
    if (openedInFullScreen && !isOpening) showStartScreen("ready");
  });

  whenEditorIsReady.then((isReady) => showStartScreen(isReady ? "ready" : "failed"));
}
