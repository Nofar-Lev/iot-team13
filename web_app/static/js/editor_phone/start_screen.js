// The start screen: one button that opens the editing screen in full screen.
//
// A page may only go full screen after a tap, so the editor cannot open that way by itself.
// Leaving full screen brings the start screen back. The layout being edited is not touched by
// any of this: unsaved changes are still there when the editing screen is opened again.

import { enterFullScreenSideways, onLeavingFullScreen } from "./full_screen_sideways.js";

/**
 * startScreen, editingScreen: the two elements, of which one shows at a time.
 * openButton:                 the button on the start screen.
 */
export function setUpStartScreen({ startScreen, editingScreen, openButton }) {
  let openedInFullScreen = false;

  function showEditingScreen() {
    startScreen.hidden = true;
    editingScreen.hidden = false;
    document.body.dataset.showing = "editing";
  }

  function showStartScreen() {
    editingScreen.hidden = true;
    startScreen.hidden = false;
    document.body.dataset.showing = "start";
  }

  openButton.addEventListener("click", async () => {
    openedInFullScreen = await enterFullScreenSideways();
    showEditingScreen();
  });

  // Only a page that was in full screen goes back to the start screen when full screen ends.
  // Where full screen never happened, there is nothing to leave.
  onLeavingFullScreen(() => {
    if (openedInFullScreen) showStartScreen();
  });

  showStartScreen();
}
