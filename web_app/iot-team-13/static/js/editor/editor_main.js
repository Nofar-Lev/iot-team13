// The editor page: connects the editor's parts to one another.
//
//   editing_session.js   this page's part in "one editor at a time": asking to be the editor
//                        in use, keeping the server's draft up to date, taking over (in
//                        ../editing/, like everything the phone editor uses too)
//   session_messages.js, dialog.js   what the session's messages say, and the dialog they
//                        are shown in (../editing/)
//   editor_state.js      the layout being edited, and the rules for changing it (../editing/)
//   widget_palette.js    the list of widgets on the left
//   drag_and_drop.js     dragging from the list and on the display
//   screens_bar.js       moving between screens, adding and removing them
//   widget_settings_form.js  the selected widget's settings (../editing/)
//   background_picker.js the current screen's background
//   saving.js, leaving.js    Save and Discard, and leaving with unsaved changes (../editing/)
//   save_bar.js          the Save and Discard buttons, and the "unsaved changes" mark
//
// The display in the middle is drawn by the same module the device uses (display_view.js).

import { el } from "../common/dom.js";
import { icon } from "../common/icons.js";
import { fetchCatalog, fetchDemoData, fetchSavedLayout } from "../common/server_api.js";
import { showToast } from "../common/toast.js";
import { createDisplayView } from "../display/display_view.js";
import { keepDisplayFitted } from "../display/scale_to_fit.js";
import { createWidget } from "../display/widgets/index.js";
import { createDialog } from "../editing/dialog.js";
import { createEditingSession } from "../editing/editing_session.js";
import { createEditorState } from "../editing/editor_state.js";
import { createLeaving } from "../editing/leaving.js";
import { createSaving } from "../editing/saving.js";
import { messageFor } from "../editing/session_messages.js";
import { setUpWidgetSettingsForm } from "../editing/widget_settings_form.js";
import { setUpBackgroundPicker } from "./background_picker.js";
import { setUpDragging } from "./drag_and_drop.js";
import { setUpSaveBar } from "./save_bar.js";
import { setUpScreensBar } from "./screens_bar.js";
import { buildWidgetPalette } from "./widget_palette.js";

// The display is shown larger than the real screen, for comfort, up to this zoom.
const LARGEST_ZOOM = 2;
// Page pixels kept free around the display.
const ROOM_AROUND_DISPLAY = 28;

async function startEditor() {
  const [catalog, demoData, saved] = await Promise.all([fetchCatalog(), fetchDemoData(), fetchSavedLayout()]);

  // The display in the middle. Until this page is the editor in use, it shows the saved
  // layout as a picture, behind whatever the page has to ask first.
  const stage = document.getElementById("editor-stage");
  const displayView = createDisplayView({ catalog, demoData });
  stage.append(displayView.frame);
  keepDisplayFitted(displayView.frame, stage, { margin: ROOM_AROUND_DISPLAY, largestZoom: LARGEST_ZOOM });
  displayView.showScreen(saved.layout.screens[0]);

  const dialog = createDialog({
    holder: document.body,
    elementsBehind: [document.querySelector(".top-bar"), document.querySelector(".editor")],
  });

  // The live channel also says whether a display is connected, so that the message after a
  // Save can say what will happen.
  let displayIsOnline = false;
  let isEditorBuilt = false;

  const session = createEditingSession({
    onNews(name, details) {
      if (name === "hello") displayIsOnline = details.display_online;
      if (name === "display") displayIsOnline = details.online;
    },
    onSituation(situation) {
      if (situation.name === "editing" && !isEditorBuilt) {
        isEditorBuilt = true;
        buildEditor({
          catalog, demoData, displayView, dialog, session, goHome,
          savedLayout: situation.saved.layout,
          draftLayout: situation.draft,
          isDisplayOnline: () => displayIsOnline,
        });
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

/** Build the editor itself. Called once, when this page becomes the editor in use. */
function buildEditor({ catalog, demoData, displayView, dialog, session, goHome, savedLayout, draftLayout, isDisplayOnline }) {
  const state = createEditorState({ catalog, savedLayout, draftLayout });

  // Every change of the layout goes to the server's draft. The session sends it only if the
  // layout really differs from what the server has.
  state.subscribe(() => session.layoutChanged(state.layout()));

  // --- The display in the middle --------------------------------------------------------------

  function markSelectedWidget() {
    for (const element of displayView.widgetElements()) {
      element.classList.remove("widget--selected");
      element.querySelector(".widget__remove")?.remove();
    }
    const index = state.selectedIndex();
    if (index === null) return;

    const removeButton = el("button", "widget__remove");
    removeButton.type = "button";
    removeButton.setAttribute("aria-label", "Remove widget");
    removeButton.append(icon("close"));
    removeButton.addEventListener("click", () => state.removeWidget(index));

    const selected = displayView.widgetElements()[index];
    selected.classList.add("widget--selected");
    selected.append(removeButton);
  }

  function drawCurrentScreen() {
    displayView.showScreen(state.currentScreen());
    markSelectedWidget();
  }

  state.subscribe((kindOfChange) => {
    // A change of selection must not redraw the widgets: the user may be in the middle of
    // pressing on one of them.
    if (kindOfChange === "selection") markSelectedWidget();
    else drawCurrentScreen();
  });
  drawCurrentScreen();

  // --- The parts around it --------------------------------------------------------------------

  const dragging = setUpDragging({
    state,
    displayView,
    createGhostPicture(widget) {
      const drawn = createWidget(widget, { cellPixels: catalog.grid.cell_pixels, demoData });
      drawn.element.style.left = "0";
      drawn.element.style.top = "0";
      return drawn.element;
    },
  });
  dragging.onPaletteClick = (widget) => {
    const wasAdded = state.addWidgetAnywhere(widget.type, widget.size);
    if (!wasAdded) showToast("This screen has no room for that widget.", "problem");
  };

  buildWidgetPalette(document.getElementById("widget-palette"), {
    catalog,
    demoData,
    onPointerDown: dragging.pressOnPaletteEntry,
  });
  setUpScreensBar(document.getElementById("screens-bar"), state);
  setUpWidgetSettingsForm(document.getElementById("settings-panel"), state);
  setUpBackgroundPicker(document.getElementById("background-picker"), state, catalog);

  const saving = createSaving({ state, session, isDisplayOnline });
  setUpSaveBar(
    {
      saveButton: document.getElementById("save-button"),
      discardButton: document.getElementById("discard-button"),
      unsavedMark: document.getElementById("unsaved-mark"),
    },
    state,
    saving,
    { isDialogShowing: dialog.isShowing },
  );

  // The Home link: with unsaved changes, it asks what should happen to them.
  const leave = createLeaving({ state, saving, dialog, goHome });
  document.getElementById("home-link").addEventListener("click", (event) => {
    event.preventDefault();
    leave();
  });

  setUpKeyboard(state, { isDialogShowing: dialog.isShowing });
  document.body.dataset.ready = "true";
}

/** Delete removes the selected widget, the arrow keys move it, Escape lets go of it. */
function setUpKeyboard(state, { isDialogShowing }) {
  const ARROW_STEPS = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] };

  window.addEventListener("keydown", (event) => {
    // While a dialog covers the editor, the keys are not for the widgets behind it.
    if (isDialogShowing()) return;
    // Keys typed into a form field belong to the field.
    if (event.target.closest("input, select, textarea")) return;
    const widget = state.selectedWidget();
    if (!widget) return;

    // Only the Delete key removes, not Backspace: there is no undo, and Backspace is too easy
    // to press while thinking the cursor is still in a text box.
    if (event.key === "Delete") {
      event.preventDefault();
      state.removeWidget(state.selectedIndex());
    } else if (event.key === "Escape") {
      state.selectWidget(null);
    } else if (event.key in ARROW_STEPS) {
      event.preventDefault();
      const [columns, rows] = ARROW_STEPS[event.key];
      state.moveWidget(state.selectedIndex(), widget.col + columns, widget.row + rows);
    }
  });
}

startEditor().catch((problem) => {
  console.error(problem);
  showToast("The editor could not start. Is the server running?", "problem");
});
