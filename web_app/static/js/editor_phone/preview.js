// The preview: the picture of the display that the phone editor works on.
//
// It is drawn by the same module as everywhere else (display_view.js). What the phone editor
// adds is the grid, on a layer behind the widgets, and the sizing: the preview is as large as
// the room it is given.

import { el } from "../common/dom.js";
import { createDisplayView } from "../display/display_view.js";
import { keepDisplayFitted } from "../display/scale_to_fit.js";

/**
 * holder: the element the preview's picture is put into (it also holds the arrows).
 * room:   the element whose size is the room the preview may fill.
 * Returns the display view (see display_view.js).
 */
export function createPreview({ catalog, demoData, holder, room }) {
  const displayView = createDisplayView({ catalog, demoData });

  // The grid goes in first, so that every widget is drawn on top of it.
  const grid = el("div", "preview-grid");
  grid.style.setProperty("--cell-size", `${catalog.grid.cell_pixels}px`);
  displayView.display.prepend(grid);

  holder.prepend(displayView.frame);
  keepDisplayFitted(displayView.frame, room, {
    unitsWide: catalog.grid.columns * catalog.grid.cell_pixels,
    unitsHigh: catalog.grid.rows * catalog.grid.cell_pixels,
  });
  return displayView;
}
