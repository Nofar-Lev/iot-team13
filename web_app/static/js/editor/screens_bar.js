// The bar under the display: arrows and dots to move between screens, and the buttons that
// add and remove a screen.

import { el } from "../common/dom.js";
import { icon } from "../common/icons.js";
import { askForSecondClick } from "../common/second_click.js";

export function setUpScreensBar(barElement, state) {
  const previousButton = el("button", "icon-button");
  previousButton.type = "button";
  previousButton.setAttribute("aria-label", "Previous screen");
  previousButton.append(icon("back"));

  const nextButton = el("button", "icon-button");
  nextButton.type = "button";
  nextButton.setAttribute("aria-label", "Next screen");
  nextButton.append(icon("forward"));

  const dots = el("div", "screens-bar__dots");
  const label = el("span", "screens-bar__label");

  const addButton = el("button", "button button--quiet");
  addButton.type = "button";
  addButton.append(icon("plus"), el("span", "", "Add screen"));

  const removeButton = el("button", "button button--quiet");
  removeButton.type = "button";
  const removeLabel = el("span", "");
  removeButton.append(icon("trash"), removeLabel);

  const navigation = el("div", "screens-bar__navigation");
  navigation.append(previousButton, dots, nextButton, label);
  const actions = el("div", "screens-bar__actions");
  actions.append(addButton, removeButton);
  barElement.append(navigation, actions);

  // Removing a screen that has widgets on it needs a second click.
  const removeQuestion = askForSecondClick({
    button: removeButton,
    labelElement: removeLabel,
    usualText: "Remove screen",
    askingText: "Click again to remove",
    shouldAsk: () => state.currentScreen().widgets.length > 0,
    onConfirmed: () => state.removeCurrentScreen(),
  });

  previousButton.addEventListener("click", () => state.showScreen(state.screenIndex() - 1));
  nextButton.addEventListener("click", () => state.showScreen(state.screenIndex() + 1));
  addButton.addEventListener("click", () => state.addScreen());

  // --- Keeping the bar in step with the state -------------------------------------------------

  function redraw() {
    const count = state.screenCount();
    const current = state.screenIndex();

    dots.replaceChildren();
    for (let index = 0; index < count; index += 1) {
      const dot = el("button", `screens-bar__dot${index === current ? " screens-bar__dot--current" : ""}`);
      dot.type = "button";
      dot.setAttribute("aria-label", `Screen ${index + 1}`);
      dot.addEventListener("click", () => state.showScreen(index));
      dots.append(dot);
    }

    label.textContent = `Screen ${current + 1} of ${count}`;
    previousButton.disabled = current === 0;
    nextButton.disabled = current === count - 1;
    addButton.disabled = !state.canAddScreen();
    removeButton.disabled = !state.canRemoveScreen();
  }

  state.subscribe((kindOfChange) => {
    if (kindOfChange === "screen" || kindOfChange === "saved") {
      removeQuestion.reset();
      redraw();
    }
  });
  redraw();
}
