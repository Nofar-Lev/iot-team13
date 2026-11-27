// The panel's list of backgrounds for the current screen, reached from "Backgrounds".
//
// Each background is a small swatch: a slice of the picture with its name on it. That is
// enough to give its mood; the preview next to the panel shows the whole picture as soon as
// one is tapped.

import { el } from "../common/dom.js";
import { topLineWithBack } from "./panel.js";

/** onBack(): back to the main menu. */
export function createBackgroundsScreen({ panel, state, catalog, onBack }) {
  function show() {
    const current = state.currentScreen().background;

    const swatches = el("div", "swatches");
    for (const background of catalog.backgrounds) {
      const isCurrent = background.id === current;
      const swatch = el("button", `swatch${isCurrent ? " swatch--current" : ""}`, background.name);
      swatch.type = "button";
      swatch.dataset.backgroundId = background.id;
      swatch.setAttribute("aria-pressed", String(isCurrent));
      swatch.style.backgroundImage = `url("static/backgrounds/${background.file}")`;
      swatch.addEventListener("click", () => state.setBackground(background.id));
      swatches.append(swatch);
    }

    panel.show("backgrounds", {
      top: topLineWithBack({ title: "Backgrounds", onBack }),
      body: [swatches],
    });
  }

  return { show };
}
