// The panel on the right of the phone editor. It is always there, and shows one thing at a
// time: the main menu, or (later) the options of what is selected.
//
// What it shows is given as up to three parts: the top line, the body, and the foot. The body
// is the only part that may scroll.

import { el } from "../common/dom.js";

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
