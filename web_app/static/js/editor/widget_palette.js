// The list of widgets on the left of the editor: one entry per widget type and size, each
// shown as a small picture of the real widget.

import { el } from "../common/dom.js";
import { parseSize } from "../common/grid.js";
import { defaultSettings } from "../editing/editor_state.js";
import { createWidgetPicture } from "../editing/widget_picture.js";

/**
 * Fill the list.
 * onPointerDown(event, { type, size }, entryElement) is called when the user presses on an
 * entry; the dragging code takes it from there.
 */
export function buildWidgetPalette(listElement, { catalog, demoData, onPointerDown }) {
  for (const catalogWidget of catalog.widgets) {
    for (const size of catalogWidget.sizes) {
      const { columns } = parseSize(size);
      const widget = { type: catalogWidget.type, size, settings: defaultSettings(catalogWidget) };

      const entry = el("button", `palette-entry palette-entry--${columns}-wide`);
      entry.type = "button";
      entry.dataset.widgetType = catalogWidget.type;
      entry.dataset.widgetSize = size;
      entry.title = "Drag onto the display, or click to add";
      entry.append(
        createWidgetPicture(widget, { catalog, demoData }),
        el("span", "palette-entry__name", `${catalogWidget.name} · ${size.replace("x", "×")}`),
      );
      entry.addEventListener("pointerdown", (event) => onPointerDown(event, widget, entry));
      listElement.append(entry);
    }
  }
}
