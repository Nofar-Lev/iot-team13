// The drawing module: turns one screen of a layout into a picture of the display.
//
// The editor's preview, the home page's preview and the device page all use this file, so the
// three always agree.
//
// The display is built as a box of exactly 480x320 units, with every widget placed by its
// cell. The box sits in a "frame", and the frame zooms the whole box as one piece (see
// scale_to_fit.js), so the display looks the same at every size.

import { el } from "../common/dom.js";
import { everySecond } from "./every_second.js";
import { createWidget } from "./widgets/index.js";

/**
 * catalog, demoData: as the server gives them.
 * Returns:
 *   frame          the element to put in the page
 *   overlay        an empty layer above the widgets, for a page's own extras (the editor's
 *                  grid lines, the device's connection icon)
 *   showScreen(screen)   draw one screen: { background, widgets }
 *   widgetElements()     the widgets' elements, in the same order as screen.widgets
 *   stop()               stop the clock ticking, when the display is no longer shown
 */
export function createDisplayView({ catalog, demoData }) {
  const cellPixels = catalog.grid.cell_pixels;
  const backgroundFiles = new Map(catalog.backgrounds.map((entry) => [entry.id, entry.file]));

  const frame = el("div", "display-frame");
  const display = el("div", "display");
  const widgetLayer = el("div", "display__widgets");
  const overlay = el("div", "display__overlay");
  const width = `${catalog.grid.columns * cellPixels}px`;
  const height = `${catalog.grid.rows * cellPixels}px`;
  display.style.width = width;
  display.style.height = height;
  frame.style.setProperty("--display-width", width);
  frame.style.setProperty("--display-height", height);
  display.append(widgetLayer, overlay);
  frame.append(display);

  let shownWidgets = [];

  function showScreen(screen) {
    const backgroundFile = backgroundFiles.get(screen.background);
    display.style.backgroundImage = backgroundFile ? `url("static/backgrounds/${backgroundFile}")` : "none";

    shownWidgets = screen.widgets.map((widget, index) => {
      const drawn = createWidget(widget, { cellPixels, demoData });
      drawn.element.style.left = `${widget.col * cellPixels}px`;
      drawn.element.style.top = `${widget.row * cellPixels}px`;
      drawn.element.dataset.widgetIndex = String(index);
      return drawn;
    });
    widgetLayer.replaceChildren(...shownWidgets.map((drawn) => drawn.element));
  }

  const stopTicking = everySecond((now) => {
    for (const drawn of shownWidgets) {
      if (drawn.update) drawn.update(now);
    }
  });

  return {
    frame,
    display,
    overlay,
    showScreen,
    widgetElements: () => shownWidgets.map((drawn) => drawn.element),
    stop: stopTicking,
  };
}

// The background pictures that were fetched ahead. They are kept here for as long as the page
// lives: a picture that nothing holds on to may be dropped by the browser, and fetched again.
const backgroundsFetchedAhead = new Map();

/**
 * Ask the browser to fetch every background now, so switching screens never shows a blank.
 * Returns a promise that is done when every picture has arrived (or failed to), for a page
 * that wants to wait for them.
 */
export function preloadBackgrounds(catalog) {
  const arrivals = catalog.backgrounds.map((background) => {
    const address = `static/backgrounds/${background.file}`;
    if (!backgroundsFetchedAhead.has(address)) {
      const picture = new Image();
      const arrival = new Promise((done) => {
        picture.onload = done;
        picture.onerror = done;   // a missing picture must not keep a page waiting
      });
      picture.src = address;
      backgroundsFetchedAhead.set(address, { picture, arrival });
    }
    return backgroundsFetchedAhead.get(address).arrival;
  });
  return Promise.all(arrivals);
}
