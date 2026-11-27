// The row of tiny dots at the bottom of the display: one per screen, the current one bright.

import { el } from "../common/dom.js";

export function createScreenDots() {
  const holder = el("div", "screen-dots");

  function show(screenCount, currentIndex) {
    holder.replaceChildren();
    if (screenCount < 2) return;   // one screen needs no dots
    for (let index = 0; index < screenCount; index += 1) {
      const isCurrent = index === currentIndex;
      holder.append(el("span", `screen-dots__dot${isCurrent ? " screen-dots__dot--current" : ""}`));
    }
  }

  return { element: holder, show };
}
