// Shared by the desktop editor and the phone editor: the rules of editing are the same for
// both, so they are written once, here.
//
// What the editor is working on: the layout being edited, which screen is showing, and which
// widget is selected. Every change to the layout goes through this file, so the rules (inside
// the grid, no overlaps, a limited number of screens) are kept in one place.
//
// No page elements here, so it is easy to test. The parts of the page listen for changes with
// subscribe() and redraw themselves.
//
// The kinds of change a listener is told about:
//   "screen"      another screen is showing, or screens were added or removed
//   "widgets"     a widget was added, moved or removed on the current screen
//   "settings"    a setting of the selected widget changed
//   "background"  the current screen's background changed
//   "selection"   another widget (or none) is selected
//   "saved"       the layout was saved, or the changes were discarded

import { canPlace, firstFreePlace } from "../common/grid.js";

const copyOf = (value) => JSON.parse(JSON.stringify(value));

/** The settings a new widget of this type starts with: every setting at its default. */
export function defaultSettings(catalogWidget) {
  return Object.fromEntries(catalogWidget.settings.map((setting) => [setting.key, setting.default]));
}

export function createEditorState({ catalog, savedLayout }) {
  const grid = { columns: catalog.grid.columns, rows: catalog.grid.rows };
  const catalogWidgets = new Map(catalog.widgets.map((entry) => [entry.type, entry]));

  let saved = copyOf(savedLayout);   // what the server has
  let draft = copyOf(savedLayout);   // what the user is editing
  let screenIndex = 0;
  let selectedIndex = null;

  const listeners = new Set();
  const tell = (kindOfChange) => {
    for (const listener of listeners) listener(kindOfChange);
  };

  const currentScreen = () => draft.screens[screenIndex];
  const isWidgetIndex = (index) => Number.isInteger(index) && index >= 0 && index < currentScreen().widgets.length;

  // --- Screens -------------------------------------------------------------------------------

  function showScreen(index) {
    if (index < 0 || index >= draft.screens.length || index === screenIndex) return false;
    screenIndex = index;
    selectedIndex = null;
    tell("screen");
    return true;
  }

  const canAddScreen = () => draft.screens.length < catalog.max_screens;
  const canRemoveScreen = () => draft.screens.length > 1;

  /** Add an empty screen after the current one, and show it. */
  function addScreen() {
    if (!canAddScreen()) return false;
    // Start with a background no other screen uses, when there is one.
    const usedBackgrounds = new Set(draft.screens.map((screen) => screen.background));
    const unused = catalog.backgrounds.find((background) => !usedBackgrounds.has(background.id));
    const background = unused ? unused.id : currentScreen().background;

    draft.screens.splice(screenIndex + 1, 0, { background, widgets: [] });
    screenIndex += 1;
    selectedIndex = null;
    tell("screen");
    return true;
  }

  function removeCurrentScreen() {
    if (!canRemoveScreen()) return false;
    draft.screens.splice(screenIndex, 1);
    screenIndex = Math.min(screenIndex, draft.screens.length - 1);
    selectedIndex = null;
    tell("screen");
    return true;
  }

  function setBackground(backgroundId) {
    const isKnown = catalog.backgrounds.some((background) => background.id === backgroundId);
    if (!isKnown || currentScreen().background === backgroundId) return false;
    currentScreen().background = backgroundId;
    tell("background");
    return true;
  }

  // --- Widgets -------------------------------------------------------------------------------

  /** May a widget of this size sit here? movingIndex names the widget being moved, if any. */
  function canPlaceWidget(size, col, row, movingIndex = -1) {
    return canPlace(grid, currentScreen().widgets, { size, col, row }, movingIndex);
  }

  /** Add a widget with default settings and select it. Returns false if it does not fit. */
  function addWidget(type, size, col, row) {
    const catalogWidget = catalogWidgets.get(type);
    if (!catalogWidget || !catalogWidget.sizes.includes(size)) return false;
    if (!canPlaceWidget(size, col, row)) return false;
    currentScreen().widgets.push({ type, size, col, row, settings: defaultSettings(catalogWidget) });
    selectedIndex = currentScreen().widgets.length - 1;
    tell("widgets");
    return true;
  }

  /** Add a widget at the first free place. Returns false if the screen has no room for it. */
  function addWidgetAnywhere(type, size) {
    const place = firstFreePlace(grid, currentScreen().widgets, size);
    return place !== null && addWidget(type, size, place.col, place.row);
  }

  function moveWidget(index, col, row) {
    if (!isWidgetIndex(index)) return false;
    const widget = currentScreen().widgets[index];
    if (widget.col === col && widget.row === row) return false;
    if (!canPlaceWidget(widget.size, col, row, index)) return false;
    widget.col = col;
    widget.row = row;
    tell("widgets");
    return true;
  }

  function removeWidget(index) {
    if (!isWidgetIndex(index)) return false;
    currentScreen().widgets.splice(index, 1);
    selectedIndex = null;
    tell("widgets");
    return true;
  }

  function selectWidget(index) {
    const newSelection = isWidgetIndex(index) ? index : null;
    if (newSelection === selectedIndex) return;
    selectedIndex = newSelection;
    tell("selection");
  }

  const selectedWidget = () => (selectedIndex === null ? null : currentScreen().widgets[selectedIndex]);

  /** Change one setting of the selected widget. */
  function changeSetting(key, value) {
    const widget = selectedWidget();
    if (!widget || !(key in widget.settings) || widget.settings[key] === value) return false;
    widget.settings[key] = value;
    tell("settings");
    return true;
  }

  // --- Saving --------------------------------------------------------------------------------

  const hasUnsavedChanges = () => JSON.stringify(draft) !== JSON.stringify(saved);

  /** Call after the server accepted the layout. */
  function markSaved() {
    saved = copyOf(draft);
    tell("saved");
  }

  /** Go back to what the server has. */
  function discardChanges() {
    draft = copyOf(saved);
    screenIndex = Math.min(screenIndex, draft.screens.length - 1);
    selectedIndex = null;
    tell("saved");
  }

  return {
    grid,
    catalogWidget: (type) => catalogWidgets.get(type),

    layout: () => draft,
    screenCount: () => draft.screens.length,
    screenIndex: () => screenIndex,
    currentScreen,
    selectedIndex: () => selectedIndex,
    selectedWidget,
    hasUnsavedChanges,

    showScreen,
    canAddScreen,
    addScreen,
    canRemoveScreen,
    removeCurrentScreen,
    setBackground,

    canPlaceWidget,
    addWidget,
    addWidgetAnywhere,
    moveWidget,
    removeWidget,
    selectWidget,
    changeSetting,

    markSaved,
    discardChanges,

    /** Call listener(kindOfChange) after every change. Returns a function that stops it. */
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
  };
}
