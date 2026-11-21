// The panel's list of one widget's sizes, for widgets that have more than one (the clock, the
// weather). A tap on a size adds the widget in that size at the first free place. A size that
// has no room on the current screen is greyed out.

import { topLineWithBack } from "./panel.js";
import { sizeAsText, widgetRow } from "./widget_rows.js";

// What each size is called in the list. A size that is not here is called by its numbers.
const SIZE_NAMES = { "2x1": "Small", "2x2": "Tall", "4x2": "Large" };

/** onBack(): back to the list of widgets. */
export function createWidgetSizesScreen({ panel, state, catalog, demoData, onBack }) {
  function show(widgetType) {
    const catalogWidget = state.catalogWidget(widgetType);
    const rows = catalogWidget.sizes.map((size) =>
      widgetRow({
        catalog,
        demoData,
        catalogWidget,
        size,
        name: SIZE_NAMES[size] ?? sizeAsText(size),
        note: sizeAsText(size),
        hasRoom: state.hasRoomFor(size),
        // The new widget is selected, so the panel moves on to its options by itself.
        onChoose: () => state.addWidgetAnywhere(widgetType, size),
      }),
    );

    panel.show("widget-sizes", {
      top: topLineWithBack({ title: catalogWidget.name, onBack }),
      body: rows,
    });
  }

  return { show };
}
