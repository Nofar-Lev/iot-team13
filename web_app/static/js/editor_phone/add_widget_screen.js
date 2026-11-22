// The panel's list of widgets, reached from "Add widget".
//
// One row per kind of widget. A tap on a widget that has one size adds it at the first free
// place; press and hold lifts it, to be carried to a place of the user's choosing. A widget
// that has several sizes shows its sizes first (widget_sizes_screen.js), and is carried from
// there. A widget that has no room on the current screen, in any of its sizes, is greyed out.

import { el } from "../common/dom.js";
import { topLineWithBack } from "./panel.js";
import { sizeAsText, widgetRow } from "./widget_rows.js";

/**
 * onBack():                   back to the main menu.
 * onChooseSizes(widgetType):  the user chose a widget that has several sizes.
 * makeCarriable:              makes a row's widget carriable (carrying_from_list.js).
 */
export function createAddWidgetScreen({ panel, state, catalog, demoData, onBack, onChooseSizes, makeCarriable }) {
  function show() {
    const rows = catalog.widgets.map((catalogWidget) => {
      const hasSeveralSizes = catalogWidget.sizes.length > 1;
      return widgetRow({
        catalog,
        demoData,
        catalogWidget,
        size: catalogWidget.sizes[0],
        name: catalogWidget.name,
        note: hasSeveralSizes ? `${catalogWidget.sizes.length} sizes ›` : sizeAsText(catalogWidget.sizes[0]),
        hasRoom: catalogWidget.sizes.some((size) => state.hasRoomFor(size)),
        onChoose() {
          if (hasSeveralSizes) onChooseSizes(catalogWidget.type);
          // The new widget is selected, so the panel moves on to its options by itself.
          else state.addWidgetAnywhere(catalogWidget.type, catalogWidget.sizes[0]);
        },
        // Which size to carry is only known for a widget that has one.
        makeCarriable: hasSeveralSizes ? null : makeCarriable,
      });
    });

    panel.show("add-widget", {
      top: topLineWithBack({ title: "Add a widget", onBack }),
      body: [el("p", "panel__hint", "Tap to add. Hold to carry it to its place."), ...rows],
    });
  }

  return { show };
}
