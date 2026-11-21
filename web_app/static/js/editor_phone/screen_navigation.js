// Moving between screens: the two round arrows on the preview's side edges, the dots under
// it, and the swipe. On the last screen the right arrow adds a screen.

import { el } from "../common/dom.js";
import { icon } from "../common/icons.js";
import { watchForSwipes } from "./screen_swipe.js";

/**
 * state:           the editor's state (editing/editor_state.js).
 * previousButton, nextButton: the two arrows.
 * dots:            the element that holds one dot per screen.
 * swipeArea:       the element on which a sideways swipe changes screen.
 * onAddScreen():   called when the right arrow is pressed on the last screen.
 */
export function setUpScreenNavigation({ state, previousButton, nextButton, dots, swipeArea, onAddScreen }) {
  const isOnLastScreen = () => state.screenIndex() === state.screenCount() - 1;

  function redraw() {
    const current = state.screenIndex();

    previousButton.replaceChildren(icon("back"));
    previousButton.setAttribute("aria-label", "Previous screen");
    previousButton.disabled = current === 0;

    // The right arrow: the next screen, or on the last screen, a new one.
    const addsAScreen = isOnLastScreen();
    nextButton.replaceChildren(icon(addsAScreen ? "plus" : "forward"));
    nextButton.setAttribute("aria-label", addsAScreen ? "Add a screen" : "Next screen");
    nextButton.classList.toggle("preview__arrow--adds-a-screen", addsAScreen);
    nextButton.dataset.does = addsAScreen ? "add-screen" : "next-screen";
    nextButton.disabled = addsAScreen && !state.canAddScreen();

    dots.replaceChildren();
    for (let index = 0; index < state.screenCount(); index += 1) {
      dots.append(el("span", `screen-dots__dot${index === current ? " screen-dots__dot--current" : ""}`));
    }
  }

  previousButton.addEventListener("click", () => state.showScreen(state.screenIndex() - 1));
  nextButton.addEventListener("click", () => {
    if (isOnLastScreen()) onAddScreen();
    else state.showScreen(state.screenIndex() + 1);
  });

  // A swipe only moves between the screens that exist. It never adds one.
  watchForSwipes(swipeArea, { onStep: (step) => state.showScreen(state.screenIndex() + step) });

  state.subscribe((kindOfChange) => {
    if (kindOfChange === "screen" || kindOfChange === "saved") redraw();
  });
  redraw();
}
