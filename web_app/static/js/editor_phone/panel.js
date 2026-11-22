// The panel on the right of the phone editor. It is always there, and shows one thing at a
// time: the main menu, a list to choose from, or the options of the selected widget.
// panel_router.js decides which.
//
// What it shows is given as up to three parts: the top line, the body, and the foot. The body
// is the only part that may scroll.

import { el } from "../common/dom.js";
import { icon } from "../common/icons.js";

/**
 * The top line of every panel screen except the main menu: a Back arrow with the screen's
 * name, and optionally a short note on the right. The arrow and the name are one button.
 * It says "Back" and not "Done": whatever was changed on the screen is already applied.
 */
export function topLineWithBack({ title, note = "", onBack }) {
  const back = el("button", "panel__back");
  back.type = "button";
  back.id = "panel-back-button";
  back.setAttribute("aria-label", `Back from ${title}`);
  back.append(icon("back"), el("span", "panel__back-title", title));
  back.addEventListener("click", onBack);
  return note ? [back, el("span", "panel__top-note", note)] : [back];
}

export function createPanel(panelElement) {
  const top = el("div", "panel__top");
  const body = el("div", "panel__body");
  const foot = el("div", "panel__foot");
  panelElement.replaceChildren(top, body, foot);

  return {
    /**
     * name:  what is being shown ("main-menu", ...), for styles and tests.
     * parts: { top, body, foot }, each a list of elements. A part that is left out is empty;
     *        an empty foot is not shown at all.
     */
    show(name, { top: topParts = [], body: bodyParts = [], foot: footParts = [] }) {
      top.replaceChildren(...topParts);
      body.replaceChildren(...bodyParts);
      foot.replaceChildren(...footParts);
      foot.hidden = footParts.length === 0;
      body.scrollTop = 0;
      panelElement.dataset.showing = name;
    },
  };
}
