// Carrying a new widget out of the panel's list and onto the preview.
//
// A tap on a row adds the widget at the first free place. Press and hold lifts it instead: a
// small picture follows the finger, the ghost shows where it would land on the preview, and it
// is added where the finger is lifted. Lifted anywhere else, nothing is added.

import { parseSize } from "../common/grid.js";
import { createWidget } from "../display/widgets/index.js";
import { defaultSettings } from "../editing/editor_state.js";
import { watchPresses } from "./press_and_hold.js";

/**
 * Returns makeCarriable(row, catalogWidget, size): call it for every row of a list whose
 * widget may be carried.
 */
export function createCarryingFromList({ state, carrying, catalog, demoData }) {
  return function makeCarriable(row, catalogWidget, size) {
    const { columns, rows } = parseSize(size);

    watchPresses(row, {
      mayHold: () => true,

      onHoldStart(event) {
        row.classList.add("widget-row--being-carried");

        // Under the finger: a copy of the row's small picture.
        const floating = row.querySelector(".widget-picture").cloneNode(true);
        floating.classList.add("carry-floating");

        // On the preview: the widget at its real size, with the settings it will start with.
        const drawn = createWidget(
          { type: catalogWidget.type, size, settings: defaultSettings(catalogWidget) },
          { cellPixels: catalog.grid.cell_pixels, demoData },
        );
        drawn.element.style.left = "0";
        drawn.element.style.top = "0";

        carrying.start({
          size,
          grabbedAt: { x: columns / 2, y: rows / 2 },   // a new widget is held by its middle
          movingIndex: -1,
          picture: drawn.element,
          floating,
        }, event);
      },

      onHoldMove: (event) => carrying.moveTo(event),

      onHoldEnd() {
        const place = carrying.end();
        row.classList.remove("widget-row--being-carried");
        // The new widget is selected, so the panel moves on to its options by itself.
        if (place) state.addWidget(catalogWidget.type, size, place.col, place.row);
      },

      onHoldCancel() {
        carrying.cancel();
        row.classList.remove("widget-row--being-carried");
      },
      // No onShortPress: a tap on the row is the row's own "click".
    });
  };
}
