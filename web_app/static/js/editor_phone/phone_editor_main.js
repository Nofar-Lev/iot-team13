// The phone editor: connects its parts to one another.
//
//   start_screen.js          the one button that opens the editing screen in full screen
//   full_screen_sideways.js  asking the browser for full screen and a sideways picture
//   preview.js               the picture of the display, with its grid, sized to the screen
//   screen_navigation.js     the round arrows, the dots, and the swipe between screens
//   screen_swipe.js          what counts as a swipe
//   selection_by_tap.js      a tap on a widget selects it; a tap elsewhere lets go of it
//   panel.js                 the panel on the right
//   panel_router.js          which screen the panel shows
//   main_menu.js             the panel while nothing is selected
//   add_widget_screen.js     the list of widgets            (uses widget_rows.js)
//   widget_sizes_screen.js   the sizes of one widget        (uses widget_rows.js)
//   widget_options_screen.js the selected widget's settings
//   backgrounds_screen.js    the backgrounds of the current screen
//   saving.js, leaving.js    saving the layout; leaving with unsaved changes
//
// The rules of editing, the settings form and the small widget pictures (../editing/) and the
// drawing of the display (../display/) are the same ones the desktop editor uses.

import { openLiveChannel } from "../common/live_channel.js";
import { fetchCatalog, fetchDemoData, fetchSavedLayout } from "../common/server_api.js";
import { showToast } from "../common/toast.js";
import { createEditorState } from "../editing/editor_state.js";
import { createAddWidgetScreen } from "./add_widget_screen.js";
import { createBackgroundsScreen } from "./backgrounds_screen.js";
import { guardUnsavedChanges } from "./leaving.js";
import { createMainMenuScreen } from "./main_menu.js";
import { createPanel } from "./panel.js";
import { createPanelRouter } from "./panel_router.js";
import { createPreview } from "./preview.js";
import { createSaving } from "./saving.js";
import { setUpScreenNavigation } from "./screen_navigation.js";
import { setUpSelectionByTap } from "./selection_by_tap.js";
import { setUpStartScreen } from "./start_screen.js";
import { createWidgetOptionsScreen } from "./widget_options_screen.js";
import { createWidgetSizesScreen } from "./widget_sizes_screen.js";

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
    swipeArea: displayView.frame,
    onAddScreen: () => state.addScreen(),
  });

  // --- Saving, and whether a display is connected to hear about it --------------------------------

  let displayIsOnline = false;
  openLiveChannel({
    role: "editor",
    onNews(name, details) {
      if (name === "hello") displayIsOnline = details.display_online;
      if (name === "display") displayIsOnline = details.online;
    },
  });
  const saving = createSaving({ state, isDisplayOnline: () => displayIsOnline });
  const unsavedChangesGuard = guardUnsavedChanges(state);

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
        onGoHome: () => unsavedChangesGuard.leaveTo("/"),
      }),
      addWidget: createAddWidgetScreen({
        panel,
        state,
        catalog,
        demoData,
        onBack: backToMainMenu,
        onChooseSizes: (widgetType) => router.openWidgetSizes(widgetType),
      }),
      widgetSizes: createWidgetSizesScreen({ panel, state, catalog, demoData, onBack: () => router.openAddWidget() }),
      widgetOptions: createWidgetOptionsScreen({ panel, state, onBack: backToMainMenu }),
      backgrounds: createBackgroundsScreen({ panel, state, catalog, onBack: backToMainMenu }),
    },
  });

  setUpSelectionByTap({
    stage: document.getElementById("stage"),
    previewFrame: displayView.frame,
    state,
    onTapOutside: backToMainMenu,
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

  document.body.dataset.ready = "true";
}

startPhoneEditor().catch((problem) => {
  console.error(problem);
  showToast("The editor could not start. Is the server running?", "problem");
});
