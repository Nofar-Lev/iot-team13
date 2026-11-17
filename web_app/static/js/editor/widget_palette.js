// The list of widgets on the left of the editor: one entry per widget type and size, each
// shown as a small picture of the real widget.

import { el } from "../common/dom.js";
import { parseSize } from "../common/grid.js";
import { setDisplayZoom } from "../display/scale_to_fit.js";
import { createWidget } from "../display/widgets/index.js";
import { defaultSettings } from "./editor_state.js";

// The small pictures are drawn at this share of the display's real size.
const PICTURE_ZOOM = 0.5;

/** A small picture of one widget, drawn by the same code as the display. */
export function createWidgetPicture({ type, size, settings }, { catalog, demoData }) {
  const cellPixels = catalog.grid.cell_pixels;
  const { columns, rows } = parseSize(size);
  const drawn = createWidget({ type, size, settings }, { cellPixels, demoData });

  // The same frame-and-box pair as the display, so the same styles and zooming apply.
  const frame = el("div", "display-frame widget-picture");
  frame.style.setProperty("--display-width", `${columns * cellPixels}px`);
  frame.style.setProperty("--display-height", `${rows * cellPixels}px`);
  setDisplayZoom(frame, PICTURE_ZOOM);

  const box = el("div", "display widget-picture__box");
  box.style.width = `${columns * cellPixels}px`;
  box.style.height = `${rows * cellPixels}px`;
  drawn.element.style.left = "0";
  drawn.element.style.top = "0";
  box.append(drawn.element);
  frame.append(box);
  return frame;
}

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
