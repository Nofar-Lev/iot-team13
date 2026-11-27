// The phone editor: connects its parts to one another.
//
//   start_screen.js          "Loading editor..." until the editor is ready, then the one
//                            button that opens the editing screen in full screen
//   full_screen_sideways.js  asking the browser for full screen and a sideways picture
//   preview.js               the picture of the display, with its grid, sized to the screen
//   screen_navigation.js     the round arrows and the dots between screens
//   preview_touches.js       a touch on the preview: tap to select, swipe between screens,
//                            press and hold to move a widget
//   screen_swipe.js          what counts as a swipe
//   press_and_hold.js        what counts as a hold
//   carrying.js              what is shown while a widget is carried, and where it may land
//   carrying_from_list.js    carrying a new widget out of the panel's list
//   taps_beside_the_preview.js  a tap next to the preview lets go of the selected widget
//   panel.js                 the panel on the right
//   panel_router.js          which screen the panel shows
//   main_menu.js             the panel while nothing is selected
//   add_widget_screen.js     the list of widgets            (uses widget_rows.js)
//   widget_sizes_screen.js   the sizes of one widget        (uses widget_rows.js)
//   widget_options_screen.js the selected widget's settings
//   backgrounds_screen.js    the backgrounds of the current screen
//
// And from ../editing/, shared with the desktop editor: the rules of editing, the settings
// form and the small widget pictures; and this page's part in "one editor at a time":
//
//   editing_session.js       asking to be the editor in use, keeping the server's draft up
//                            to date, taking over
//   session_messages.js, dialog.js   what the session's messages say, and the dialog they
//                            are shown in
//   saving.js, leaving.js    Save and Discard, and leaving with unsaved changes
//
// The drawing of the display (../display/) is the one every page uses.

import { fetchCatalog, fetchDemoData } from "../common/server_api.js";
import { showToast } from "../common/toast.js";
import { preloadBackgrounds } from "../display/display_view.js";
import { createDialog } from "../editing/dialog.js";
import { createEditingSession } from "../editing/editing_session.js";
import { createEditorState } from "../editing/editor_state.js";
import { createLeaving } from "../editing/leaving.js";
import { createSaving } from "../editing/saving.js";
import { messageFor } from "../editing/session_messages.js";
import { createAddWidgetScreen } from "./add_widget_screen.js";
import { createBackgroundsScreen } from "./backgrounds_screen.js";
import { createCarrying } from "./carrying.js";
import { createCarryingFromList } from "./carrying_from_list.js";
import { createMainMenuScreen } from "./main_menu.js";
import { createPanel } from "./panel.js";
import { createPanelRouter } from "./panel_router.js";
import { createPreview } from "./preview.js";
import { setUpPreviewTouches } from "./preview_touches.js";
import { setUpScreenNavigation } from "./screen_navigation.js";
import { setUpStartScreen } from "./start_screen.js";
import { setUpTapsBesideThePreview } from "./taps_beside_the_preview.js";
import { createWidgetOptionsScreen } from "./widget_options_screen.js";
import { createWidgetSizesScreen } from "./widget_sizes_screen.js";

// The editor waits for the background pictures before it says it is ready, but not for ever:
// after this long it is ready anyway, and a picture still on its way appears when it arrives.
const LONGEST_WAIT_FOR_PICTURES_MS = 4000;

const wait = (milliseconds) => new Promise((done) => setTimeout(done, milliseconds));

async function startPhoneEditor() {
  const startScreen = document.getElementById("start-screen");
  const editingScreen = document.getElementById("editing-screen");

  // The start screen shows "Loading editor..." until the editor says it is ready, and then
  // the button that opens the editing screen.
  let sayWhetherTheEditorIsReady = null;
  const whenEditorIsReady = new Promise((resolve) => {
    sayWhetherTheEditorIsReady = resolve;
  });
  setUpStartScreen({
    startScreen,
    editingScreen,
    openButton: document.getElementById("open-editor-button"),
    whenEditorIsReady,
  });

  // A dialog covers whichever of the two screens is showing. A newly opened editor meets
  // its questions on the start screen; the editor in use meets them wherever it is.
  const dialog = createDialog({ holder: document.body, elementsBehind: [startScreen, editingScreen] });

  let catalog, demoData;
  try {
    [catalog, demoData] = await Promise.all([fetchCatalog(), fetchDemoData()]);
  } catch (problem) {
    sayWhetherTheEditorIsReady(false);
    throw problem;
  }
  // Every background is fetched now, while the rest goes on: the ones of every screen, and
  // the ones the Backgrounds list shows. Moving between screens then never waits for a picture.
  const backgroundsHaveArrived = preloadBackgrounds(catalog);

  // The live channel also says whether a display is connected, so that the message after a
  // Save can say what will happen.
  let displayIsOnline = false;
  let isEditorBuilt = false;

  /** This page is the editor in use: build the editing screen, and then show the button. */
  async function becomeTheEditor({ saved, draft }) {
    try {
      buildEditor({
        catalog, demoData, session, dialog, goHome,
        savedLayout: saved.layout,
        draftLayout: draft,
        isDisplayOnline: () => displayIsOnline,
      });
      await Promise.race([backgroundsHaveArrived, wait(LONGEST_WAIT_FOR_PICTURES_MS)]);
      sayWhetherTheEditorIsReady(true);
      document.body.dataset.ready = "true";
    } catch (problem) {
      sayWhetherTheEditorIsReady(false);
      console.error(problem);
    }
  }

  const session = createEditingSession({
    onNews(name, details) {
      if (name === "hello") displayIsOnline = details.display_online;
      if (name === "display") displayIsOnline = details.online;
    },
    onSituation(situation) {
      if (situation.name === "editing" && !isEditorBuilt) {
        isEditorBuilt = true;
        becomeTheEditor(situation);
      }
      const message = messageFor(situation, { session, goHome, reload: () => window.location.reload() });
      if (message) dialog.show(message);
      else dialog.close();
    },
  });

  /** Leave for the home page. The server is told first, so that it knows at once. */
  async function goHome() {
    await session.leave();
    window.location.href = "./";   // the home page: the top of the app, wherever the app is served
  }

  session.start();
}

/** Build the editing screen. Called once, when this page becomes the editor in use. */
function buildEditor({ catalog, demoData, session, dialog, goHome, savedLayout, draftLayout, isDisplayOnline }) {
  const state = createEditorState({ catalog, savedLayout, draftLayout });

  // Every change of the layout goes to the server's draft. The session sends it only if the
  // layout really differs from what the server has.
  state.subscribe(() => session.layoutChanged(state.layout()));

  // --- The preview ------------------------------------------------------------------------------

  const displayView = createPreview({
    catalog,
    demoData,
    holder: document.getElementById("preview"),
    room: document.getElementById("preview-room"),
  });

  function markSelectedWidget() {
    const selectedIndex = state.selectedIndex();
    displayView.widgetElements().forEach((element, index) => {
      element.classList.toggle("widget--selected", index === selectedIndex);
    });
  }

  function drawCurrentScreen() {
    displayView.showScreen(state.currentScreen());
    markSelectedWidget();
    document.body.dataset.screen = String(state.screenIndex());
  }

  setUpScreenNavigation({
    state,
    previousButton: document.getElementById("previous-screen-button"),
    nextButton: document.getElementById("next-screen-button"),
    dots: document.getElementById("screen-dots"),
    onAddScreen: () => state.addScreen(),
  });

  // What is shown while a widget is carried: by a hold on the preview, or out of the list.
  const carrying = createCarrying({ state, displayView });
  const makeCarriable = createCarryingFromList({ state, carrying, catalog, demoData });

  // --- Saving, discarding, and leaving ------------------------------------------------------------

  const saving = createSaving({ state, session, isDisplayOnline });
  // Home was pressed. With unsaved changes, the user chooses what happens to them first.
  const leave = createLeaving({ state, saving, dialog, goHome });

  // --- The panel --------------------------------------------------------------------------------

  const panel = createPanel(document.getElementById("panel"));
  // The screens need the router (to move between one another), and the router needs the
  // screens. So the screens are given functions that look the router up when they are called.
  let router = null;
  const backToMainMenu = () => router.backToMainMenu();

  router = createPanelRouter({
    state,
    screens: {
      mainMenu: createMainMenuScreen({
        panel,
        state,
        onAddWidget: () => router.openAddWidget(),
        onBackgrounds: () => router.openBackgrounds(),
        onSave: () => saving.save(),
        onDiscard: () => saving.discard(),
        onGoHome: leave,
      }),
      addWidget: createAddWidgetScreen({
        panel,
        state,
        catalog,
        demoData,
        onBack: backToMainMenu,
        onChooseSizes: (widgetType) => router.openWidgetSizes(widgetType),
        makeCarriable,
      }),
      widgetSizes: createWidgetSizesScreen({
        panel, state, catalog, demoData, makeCarriable, onBack: () => router.openAddWidget(),
      }),
      widgetOptions: createWidgetOptionsScreen({ panel, state, onBack: backToMainMenu }),
      backgrounds: createBackgroundsScreen({ panel, state, catalog, onBack: backToMainMenu }),
    },
  });

  setUpPreviewTouches({ state, displayView, carrying, onTapOutside: backToMainMenu });
  setUpTapsBesideThePreview({
    stage: document.getElementById("stage"),
    previewFrame: displayView.frame,
    onTapBeside: backToMainMenu,
  });

  // --- Keeping the preview in step with the state -------------------------------------------------

  state.subscribe((kindOfChange) => {
    // A change of selection only moves the ring. The widgets are not drawn again: a finger
    // may be on one of them.
    if (kindOfChange === "selection") markSelectedWidget();
    else drawCurrentScreen();
  });
  drawCurrentScreen();
  router.showWhatApplies();
}

startPhoneEditor().catch((problem) => {
  console.error(problem);
  showToast("The editor could not start. Is the server running?", "problem");
});
