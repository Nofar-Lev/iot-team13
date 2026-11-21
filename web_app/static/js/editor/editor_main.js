// The editor page: connects the editor's parts to one another.
//
//   editor_state.js      the layout being edited, and the rules for changing it (in ../editing/,
//                        because the phone editor uses the same rules)
//   widget_palette.js    the list of widgets on the left
//   drag_and_drop.js     dragging from the list and on the display
//   screens_bar.js       moving between screens, adding and removing them
//   settings_panel.js    the selected widget's settings
//   background_picker.js the current screen's background
//   save_bar.js          Save, Discard, and the "unsaved changes" mark
//
// The display in the middle is drawn by the same module the device uses (display_view.js).

import { el } from "../common/dom.js";
import { icon } from "../common/icons.js";
import { openLiveChannel } from "../common/live_channel.js";
import { fetchCatalog, fetchDemoData, fetchSavedLayout } from "../common/server_api.js";
import { showToast } from "../common/toast.js";
import { createDisplayView } from "../display/display_view.js";
import { keepDisplayFitted } from "../display/scale_to_fit.js";
import { createWidget } from "../display/widgets/index.js";
import { setUpBackgroundPicker } from "./background_picker.js";
import { setUpDragging } from "./drag_and_drop.js";
import { createEditorState } from "../editing/editor_state.js";
import { setUpSaveBar } from "./save_bar.js";
import { setUpScreensBar } from "./screens_bar.js";
import { setUpSettingsPanel } from "./settings_panel.js";
import { buildWidgetPalette } from "./widget_palette.js";

// The display is shown larger than the real screen, for comfort, up to this zoom.
const LARGEST_ZOOM = 2;
// Page pixels kept free around the display.
const ROOM_AROUND_DISPLAY = 28;

async function startEditor() {
  const [catalog, demoData, saved] = await Promise.all([fetchCatalog(), fetchDemoData(), fetchSavedLayout()]);
  const state = createEditorState({ catalog, savedLayout: saved.layout });

  // --- The display in the middle --------------------------------------------------------------

  const stage = document.getElementById("editor-stage");
  const displayView = createDisplayView({ catalog, demoData });
  stage.append(displayView.frame);
  keepDisplayFitted(displayView.frame, stage, { margin: ROOM_AROUND_DISPLAY, largestZoom: LARGEST_ZOOM });

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
  setUpSettingsPanel(document.getElementById("settings-panel"), state);
  setUpBackgroundPicker(document.getElementById("background-picker"), state, catalog);

  // The editor listens on the live channel only to know whether a display is connected, so
  // that the message after a Save can say what will happen.
  let displayIsOnline = false;
  openLiveChannel({
    role: "editor",
    onNews(name, details) {
      if (name === "hello") displayIsOnline = details.display_online;
      if (name === "display") displayIsOnline = details.online;
    },
  });

  setUpSaveBar(
    {
      saveButton: document.getElementById("save-button"),
      discardButton: document.getElementById("discard-button"),
      unsavedMark: document.getElementById("unsaved-mark"),
    },
    state,
    { isDisplayOnline: () => displayIsOnline },
  );

  setUpKeyboard(state);
  document.body.dataset.ready = "true";
}

/** Delete removes the selected widget, the arrow keys move it, Escape lets go of it. */
function setUpKeyboard(state) {
  const ARROW_STEPS = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] };

  window.addEventListener("keydown", (event) => {
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
