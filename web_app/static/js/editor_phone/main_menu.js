// The panel's main menu: what the panel shows while nothing is selected.
//
// From the top: Home; the two large buttons, Add widget and Backgrounds; Remove this screen;
// and at the bottom Discard and Save layout. Save and Discard are about the whole layout, so
// they are here and nowhere else in the panel.

import { el } from "../common/dom.js";
import { icon } from "../common/icons.js";

function largeButton(iconName, text, id) {
  const button = el("button", "menu-button");
  button.type = "button";
  button.id = id;
  button.append(icon(iconName), el("span", "", text));
  return button;
}

/**
 * state: the editor's state (editing/editor_state.js).
 * The on...() functions are called when their button is pressed.
 * Returns { parts, refresh() }: the parts to show in the panel, and a function that brings
 * the buttons in step with the state.
 */
export function buildMainMenu({ state, onAddWidget, onBackgrounds, onRemoveScreen, onSave, onDiscard }) {
  const home = el("a", "panel__home");
  home.href = "/";
  home.id = "home-link";
  home.append(icon("home"), el("span", "", "Home"));

  const addWidgetButton = largeButton("plus", "Add widget", "add-widget-button");
  const backgroundsButton = largeButton("backgrounds", "Backgrounds", "backgrounds-button");

  const removeScreenButton = el("button", "quiet-action");
  removeScreenButton.type = "button";
  removeScreenButton.id = "remove-screen-button";
  removeScreenButton.append(icon("trash"), el("span", "", "Remove this screen"));

  const discardButton = el("button", "foot-button foot-button--discard", "Discard");
  discardButton.type = "button";
  discardButton.id = "discard-button";

  const saveButton = el("button", "foot-button foot-button--save", "Save layout");
  saveButton.type = "button";
  saveButton.id = "save-button";

  addWidgetButton.addEventListener("click", onAddWidget);
  backgroundsButton.addEventListener("click", onBackgrounds);
  removeScreenButton.addEventListener("click", onRemoveScreen);
  discardButton.addEventListener("click", onDiscard);
  saveButton.addEventListener("click", onSave);

  function refresh() {
    // With nothing changed there is nothing to save and nothing to discard.
    const hasChanges = state.hasUnsavedChanges();
    saveButton.disabled = !hasChanges;
    discardButton.disabled = !hasChanges;
    // The last screen cannot be removed.
    removeScreenButton.disabled = !state.canRemoveScreen();
  }
  refresh();

  return {
    parts: {
      top: [home],
      body: [addWidgetButton, backgroundsButton, el("div", "panel__spacer"), removeScreenButton],
      foot: [discardButton, saveButton],
    },
    refresh,
  };
}
