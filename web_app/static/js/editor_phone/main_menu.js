// The panel's main menu: what the panel shows while nothing is selected.
//
// From the top: Home; the two large buttons, Add widget and Backgrounds; Remove this screen;
// and at the bottom Discard and Save layout. Save and Discard are about the whole layout, so
// they are here and nowhere else in the panel.
//
// A button that would throw work away asks for a second tap, and only when there is something
// to lose: Discard always (it is greyed out when nothing changed), and Remove this screen when
// the screen has widgets on it. Home asks too, with a dialog of its own, which is not this
// file's business: it only says that Home was pressed.

import { el } from "../common/dom.js";
import { icon } from "../common/icons.js";
import { askForSecondClick } from "../common/second_click.js";

function buttonWithIcon(className, id, iconName, text) {
  const button = el("button", className);
  button.type = "button";
  button.id = id;
  const label = el("span", "", text);
  button.append(icon(iconName), label);
  return { button, label };
}

/**
 * state:           the editor's state (editing/editor_state.js).
 * onAddWidget(), onBackgrounds(): open those screens of the panel.
 * onSave():        save the layout.
 * onGoHome():      Home was pressed.
 */
export function createMainMenuScreen({ panel, state, onAddWidget, onBackgrounds, onSave, onGoHome }) {
  const home = buttonWithIcon("panel__home", "home-button", "home", "Home");
  const addWidget = buttonWithIcon("menu-button", "add-widget-button", "plus", "Add widget");
  const backgrounds = buttonWithIcon("menu-button", "backgrounds-button", "backgrounds", "Backgrounds");
  const removeScreen = buttonWithIcon("quiet-action", "remove-screen-button", "trash", "Remove this screen");

  const discardButton = el("button", "foot-button foot-button--discard");
  discardButton.type = "button";
  discardButton.id = "discard-button";

  const saveButton = el("button", "foot-button foot-button--save", "Save layout");
  saveButton.type = "button";
  saveButton.id = "save-button";

  addWidget.button.addEventListener("click", onAddWidget);
  backgrounds.button.addEventListener("click", onBackgrounds);
  saveButton.addEventListener("click", onSave);

  home.button.addEventListener("click", onGoHome);

  const questions = [
    askForSecondClick({
      button: removeScreen.button,
      labelElement: removeScreen.label,
      usualText: "Remove this screen",
      askingText: "Tap again to remove",
      shouldAsk: () => state.currentScreen().widgets.length > 0,
      onConfirmed: () => state.removeCurrentScreen(),
    }),
    askForSecondClick({
      button: discardButton,
      labelElement: discardButton,
      usualText: "Discard",
      askingText: "Tap again",
      shouldAsk: () => true,
      onConfirmed: () => state.discardChanges(),
    }),
  ];

  /** Bring the buttons in step with the state. A question that was being asked is dropped. */
  function refresh() {
    for (const question of questions) question.reset();
    // With nothing changed there is nothing to save and nothing to discard.
    const hasChanges = state.hasUnsavedChanges();
    saveButton.disabled = !hasChanges;
    discardButton.disabled = !hasChanges;
    // The only screen cannot be removed.
    removeScreen.button.disabled = !state.canRemoveScreen();
  }

  function show() {
    refresh();
    panel.show("main-menu", {
      top: [home.button],
      body: [addWidget.button, backgrounds.button, el("div", "panel__spacer"), removeScreen.button],
      foot: [discardButton, saveButton],
    });
  }

  return { show };
}
