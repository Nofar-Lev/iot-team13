// The phone editor: connects its parts to one another.
//
//   start_screen.js          the one button that opens the editing screen in full screen
//   full_screen_sideways.js  asking the browser for full screen and a sideways picture
//   preview.js               the picture of the display, with its grid, sized to the screen
//   screen_navigation.js     the round arrows, the dots, and the swipe between screens
//   screen_swipe.js          what counts as a swipe
//   panel.js                 the panel on the right
//   main_menu.js             what the panel shows while nothing is selected
//
// The rules of editing (../editing/editor_state.js) and the drawing of the display
// (../display/) are the same ones the desktop editor uses.

import { fetchCatalog, fetchDemoData, fetchSavedLayout } from "../common/server_api.js";
import { showToast } from "../common/toast.js";
import { createEditorState } from "../editing/editor_state.js";
import { buildMainMenu } from "./main_menu.js";
import { createPanel } from "./panel.js";
import { createPreview } from "./preview.js";
import { setUpScreenNavigation } from "./screen_navigation.js";
import { setUpStartScreen } from "./start_screen.js";

/** For the buttons whose work is not built yet. They say so, and do nothing else. */
function notBuiltYet(what) {
  return () => showToast(`${what} is not built yet.`);
}

async function startPhoneEditor() {
  // The start screen works from the first moment, before anything is fetched.
  setUpStartScreen({
    startScreen: document.getElementById("start-screen"),
    editingScreen: document.getElementById("editing-screen"),
    openButton: document.getElementById("open-editor-button"),
  });

  const [catalog, demoData, saved] = await Promise.all([fetchCatalog(), fetchDemoData(), fetchSavedLayout()]);
  const state = createEditorState({ catalog, savedLayout: saved.layout });

  // --- The preview ------------------------------------------------------------------------------

  const previewHolder = document.getElementById("preview");
  const displayView = createPreview({
    catalog,
    demoData,
    holder: previewHolder,
    room: document.getElementById("preview-room"),
  });

  setUpScreenNavigation({
    state,
    previousButton: document.getElementById("previous-screen-button"),
    nextButton: document.getElementById("next-screen-button"),
    dots: document.getElementById("screen-dots"),
    swipeArea: displayView.frame,
    onAddScreen: notBuiltYet("Adding a screen"),
  });

  // --- The panel --------------------------------------------------------------------------------

  const panel = createPanel(document.getElementById("panel"));
  const mainMenu = buildMainMenu({
    state,
    onAddWidget: notBuiltYet("Adding a widget"),
    onBackgrounds: notBuiltYet("Choosing a background"),
    onRemoveScreen: notBuiltYet("Removing a screen"),
    onSave: notBuiltYet("Saving"),
    onDiscard: notBuiltYet("Discarding"),
  });
  panel.show("main-menu", mainMenu.parts);

  // --- Keeping everything in step with the state ------------------------------------------------

  function drawCurrentScreen() {
    displayView.showScreen(state.currentScreen());
    document.body.dataset.screen = String(state.screenIndex());
  }

  state.subscribe(() => {
    drawCurrentScreen();
    mainMenu.refresh();
  });
  drawCurrentScreen();

  document.body.dataset.ready = "true";
}

startPhoneEditor().catch((problem) => {
  console.error(problem);
  showToast("The editor could not start. Is the server running?", "problem");
});
