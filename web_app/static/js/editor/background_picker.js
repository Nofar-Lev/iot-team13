// The list of background pictures for the current screen.

import { el } from "../common/dom.js";

export function setUpBackgroundPicker(listElement, state, catalog) {
  const buttons = new Map();

  for (const background of catalog.backgrounds) {
    const button = el("button", "background-choice");
    button.type = "button";
    button.dataset.backgroundId = background.id;
    button.title = background.name;

    const picture = el("img", "background-choice__picture");
    picture.src = `/static/backgrounds/${background.file}`;
    picture.alt = "";
    picture.draggable = false;

    button.append(picture, el("span", "background-choice__name", background.name));
    button.addEventListener("click", () => state.setBackground(background.id));
    listElement.append(button);
    buttons.set(background.id, button);
  }

  function markCurrent() {
    const current = state.currentScreen().background;
    for (const [backgroundId, button] of buttons) {
      const isCurrent = backgroundId === current;
      button.classList.toggle("background-choice--current", isCurrent);
      button.setAttribute("aria-pressed", String(isCurrent));
    }
  }

  state.subscribe((kindOfChange) => {
    if (["background", "screen", "saved"].includes(kindOfChange)) markCurrent();
  });
  markCurrent();
}
