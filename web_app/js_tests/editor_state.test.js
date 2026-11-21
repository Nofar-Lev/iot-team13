// Tests for the editor's state: what happens to the layout when the user adds, moves and
// removes things. Run with:  node --test js_tests/
//
// They use the real widget catalog and the real default layout.

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import { createEditorState, defaultSettings } from "../static/js/editing/editor_state.js";

const readData = (name) => JSON.parse(readFileSync(new URL(`../data/${name}`, import.meta.url), "utf-8"));
const catalog = readData("widget_catalog.json");
const defaultLayout = readData("default_layout.json");

const emptyLayout = () => ({
  version: 1,
  grid: { columns: 6, rows: 4 },
  screens: [{ background: "soft-hills", widgets: [] }],
});

/** A state, and a list that collects every change it announces. */
function newState(layout = emptyLayout()) {
  const state = createEditorState({ catalog, savedLayout: layout });
  const changes = [];
  state.subscribe((kindOfChange) => changes.push(kindOfChange));
  return { state, changes };
}

// --- Starting --------------------------------------------------------------------------------

test("a new state shows the first screen, with nothing selected and nothing to save", () => {
  const { state } = newState(defaultLayout);
  assert.equal(state.screenIndex(), 0);
  assert.equal(state.selectedIndex(), null);
  assert.equal(state.hasUnsavedChanges(), false);
  assert.deepEqual(state.layout(), defaultLayout);
});

test("editing never changes the layout that was passed in", () => {
  const layout = emptyLayout();
  const { state } = newState(layout);
  state.addWidget("clock", "2x1", 0, 0);
  assert.deepEqual(layout, emptyLayout());
});

test("a new widget's settings are the catalog's defaults", () => {
  const clock = catalog.widgets.find((entry) => entry.type === "clock");
  assert.deepEqual(defaultSettings(clock), {
    format: "24h", show_seconds: false, time_mode: "automatic", offset_minutes: 0,
  });
});

// --- Widgets ---------------------------------------------------------------------------------

test("adding a widget puts it on the screen, selects it and marks the layout as changed", () => {
  const { state, changes } = newState();
  assert.equal(state.addWidget("weather", "2x2", 1, 1), true);

  assert.deepEqual(state.currentScreen().widgets, [
    { type: "weather", size: "2x2", col: 1, row: 1, settings: { city: "Haifa", units: "celsius" } },
  ]);
  assert.equal(state.selectedIndex(), 0);
  assert.equal(state.hasUnsavedChanges(), true);
  assert.deepEqual(changes, ["widgets"]);
});

test("a widget cannot be added on top of another, outside the grid, or in an unknown form", () => {
  const { state, changes } = newState();
  state.addWidget("clock", "4x2", 0, 0);
  changes.length = 0;

  assert.equal(state.addWidget("stock", "2x1", 3, 1), false);     // overlaps
  assert.equal(state.addWidget("stock", "2x1", 5, 3), false);     // leaves the grid
  assert.equal(state.addWidget("stock", "4x2", 0, 2), false);     // the stock has no 4x2 size
  assert.equal(state.addWidget("sundial", "2x1", 0, 2), false);   // no such widget
  assert.equal(state.currentScreen().widgets.length, 1);
  assert.deepEqual(changes, []);
});

test("adding anywhere uses the first free place", () => {
  const { state } = newState();
  state.addWidget("clock", "4x2", 0, 0);
  assert.equal(state.addWidgetAnywhere("stock", "2x1"), true);
  const stock = state.currentScreen().widgets[1];
  assert.deepEqual([stock.col, stock.row], [4, 0]);
});

test("adding anywhere fails when the screen has no room", () => {
  const { state } = newState();
  state.addWidget("clock", "4x2", 0, 0);
  state.addWidget("reminders", "4x2", 2, 2);
  assert.equal(state.addWidgetAnywhere("clock", "4x2"), false);
  assert.equal(state.currentScreen().widgets.length, 2);
});

test("moving a widget changes its place and keeps its settings", () => {
  const { state } = newState();
  state.addWidget("stock", "2x1", 0, 0);
  state.changeSetting("symbol", "AAPL");
  assert.equal(state.moveWidget(0, 4, 3), true);
  assert.deepEqual(state.currentScreen().widgets[0], {
    type: "stock", size: "2x1", col: 4, row: 3, settings: { symbol: "AAPL" },
  });
});

test("a widget may move to a place that overlaps only its own old place", () => {
  const { state } = newState();
  state.addWidget("clock", "4x2", 0, 0);
  assert.equal(state.moveWidget(0, 1, 1), true);
});

test("a widget cannot move onto another widget or out of the grid", () => {
  const { state } = newState();
  state.addWidget("clock", "4x2", 0, 0);
  state.addWidget("stock", "2x1", 4, 0);
  assert.equal(state.moveWidget(1, 3, 1), false);
  assert.equal(state.moveWidget(1, 5, 0), false);
  assert.equal(state.moveWidget(1, 4, -1), false);
  const stock = state.currentScreen().widgets[1];
  assert.deepEqual([stock.col, stock.row], [4, 0]);
});

test("moving a widget to where it already is changes nothing", () => {
  const { state, changes } = newState();
  state.addWidget("stock", "2x1", 0, 0);
  changes.length = 0;
  assert.equal(state.moveWidget(0, 0, 0), false);
  assert.deepEqual(changes, []);
});

test("moving a widget away and back leaves nothing to save", () => {
  const { state } = newState(defaultLayout);
  const { col, row } = state.currentScreen().widgets[1];
  state.moveWidget(1, 0, 2);
  assert.equal(state.hasUnsavedChanges(), true);
  state.moveWidget(1, col, row);
  assert.equal(state.hasUnsavedChanges(), false);
});

test("removing a widget takes it off the screen and clears the selection", () => {
  const { state } = newState();
  state.addWidget("clock", "2x1", 0, 0);
  state.addWidget("stock", "2x1", 2, 0);
  assert.equal(state.removeWidget(0), true);
  assert.deepEqual(state.currentScreen().widgets.map((widget) => widget.type), ["stock"]);
  assert.equal(state.selectedIndex(), null);
  assert.equal(state.removeWidget(5), false);
});

test("the place of a removed widget is free again", () => {
  const { state } = newState();
  state.addWidget("clock", "4x2", 0, 0);
  assert.equal(state.canPlaceWidget("2x1", 0, 0), false);
  state.removeWidget(0);
  assert.equal(state.canPlaceWidget("2x1", 0, 0), true);
});

// --- Selection and settings ------------------------------------------------------------------

test("selecting announces a change only when the selection really changes", () => {
  const { state, changes } = newState(defaultLayout);
  state.selectWidget(2);
  state.selectWidget(2);
  state.selectWidget(null);
  state.selectWidget(99);   // no such widget: the same as selecting nothing
  assert.deepEqual(changes, ["selection", "selection"]);
});

test("a setting of the selected widget can be changed", () => {
  const { state, changes } = newState();
  state.addWidget("weather", "2x1", 0, 0);
  changes.length = 0;
  assert.equal(state.changeSetting("city", "Tel Aviv"), true);
  assert.equal(state.selectedWidget().settings.city, "Tel Aviv");
  assert.deepEqual(changes, ["settings"]);
});

test("a setting cannot be changed with nothing selected, or under a name the widget lacks", () => {
  const { state } = newState();
  assert.equal(state.changeSetting("city", "Tel Aviv"), false);
  state.addWidget("weather", "2x1", 0, 0);
  assert.equal(state.changeSetting("symbol", "AAPL"), false);
  assert.deepEqual(Object.keys(state.selectedWidget().settings), ["city", "units"]);
});

// --- Screens ---------------------------------------------------------------------------------

test("showing another screen clears the selection", () => {
  const { state, changes } = newState(defaultLayout);
  state.selectWidget(0);
  changes.length = 0;
  assert.equal(state.showScreen(1), true);
  assert.equal(state.screenIndex(), 1);
  assert.equal(state.selectedIndex(), null);
  assert.deepEqual(changes, ["screen"]);
});

test("there is no screen before the first or after the last", () => {
  const { state } = newState(defaultLayout);
  assert.equal(state.showScreen(-1), false);
  assert.equal(state.showScreen(2), false);
  assert.equal(state.screenIndex(), 0);
});

test("a new screen comes after the current one, is empty, and is shown", () => {
  const { state } = newState(defaultLayout);
  assert.equal(state.addScreen(), true);
  assert.equal(state.screenCount(), 3);
  assert.equal(state.screenIndex(), 1);
  assert.deepEqual(state.currentScreen().widgets, []);
});

test("a new screen starts with a background no other screen uses", () => {
  const { state } = newState(defaultLayout);
  state.addScreen();
  const used = defaultLayout.screens.map((screen) => screen.background);
  assert.ok(!used.includes(state.currentScreen().background));
  assert.ok(catalog.backgrounds.some((background) => background.id === state.currentScreen().background));
});

test("screens can be added up to the catalog's limit and no further", () => {
  const { state } = newState();
  while (state.canAddScreen()) state.addScreen();
  assert.equal(state.screenCount(), catalog.max_screens);
  assert.equal(state.addScreen(), false);
  assert.equal(state.screenCount(), catalog.max_screens);
});

test("removing a screen shows a neighbour", () => {
  const { state } = newState(defaultLayout);
  state.showScreen(1);
  assert.equal(state.removeCurrentScreen(), true);
  assert.equal(state.screenCount(), 1);
  assert.equal(state.screenIndex(), 0);
  assert.equal(state.currentScreen().background, defaultLayout.screens[0].background);
});

test("the last screen cannot be removed", () => {
  const { state } = newState();
  assert.equal(state.canRemoveScreen(), false);
  assert.equal(state.removeCurrentScreen(), false);
  assert.equal(state.screenCount(), 1);
});

test("the background of the current screen can be changed to one from the catalog", () => {
  const { state, changes } = newState(defaultLayout);
  assert.equal(state.setBackground("forest"), true);
  assert.equal(state.currentScreen().background, "forest");
  assert.equal(state.layout().screens[1].background, defaultLayout.screens[1].background);
  assert.equal(state.setBackground("forest"), false);        // already that one
  assert.equal(state.setBackground("my-holiday"), false);    // not in the catalog
  assert.deepEqual(changes, ["background"]);
});

// --- Saving and discarding -------------------------------------------------------------------

test("after a save there is nothing left to save", () => {
  const { state, changes } = newState();
  state.addWidget("clock", "2x1", 0, 0);
  state.markSaved();
  assert.equal(state.hasUnsavedChanges(), false);
  assert.equal(changes.at(-1), "saved");
});

test("discarding goes back to the last saved layout", () => {
  const { state } = newState(defaultLayout);
  state.addScreen();
  state.addWidget("clock", "2x1", 0, 0);
  state.discardChanges();
  assert.deepEqual(state.layout(), defaultLayout);
  assert.equal(state.hasUnsavedChanges(), false);
  assert.equal(state.selectedIndex(), null);
  assert.ok(state.screenIndex() < state.screenCount());
});

test("discarding after a save goes back to the saved layout, not to the first one", () => {
  const { state } = newState();
  state.addWidget("clock", "2x1", 0, 0);
  state.markSaved();
  state.addWidget("stock", "2x1", 2, 0);
  state.discardChanges();
  assert.deepEqual(state.currentScreen().widgets.map((widget) => widget.type), ["clock"]);
});

test("a listener that unsubscribed hears nothing more", () => {
  const state = createEditorState({ catalog, savedLayout: emptyLayout() });
  const heard = [];
  const stopListening = state.subscribe((kindOfChange) => heard.push(kindOfChange));
  state.addWidget("clock", "2x1", 0, 0);
  stopListening();
  state.addWidget("stock", "2x1", 2, 0);
  assert.deepEqual(heard, ["widgets"]);
});
