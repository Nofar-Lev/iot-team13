// Shared by the desktop editor and the phone editor: a small picture of one widget, for the
// lists that widgets are chosen from. It is drawn by the same code as the display, so the
// picture is what the widget will look like.

import { el } from "../common/dom.js";
import { parseSize } from "../common/grid.js";
import { setDisplayZoom } from "../display/scale_to_fit.js";
import { createWidget } from "../display/widgets/index.js";

// Unless told otherwise, the pictures are drawn at this share of the display's real size.
const USUAL_PICTURE_ZOOM = 0.5;

/**
 * widget: { type, size, settings }.
 * zoom:   the picture's size as a share of the widget's real size on the display.
 */
export function createWidgetPicture({ type, size, settings }, { catalog, demoData, zoom = USUAL_PICTURE_ZOOM }) {
  const cellPixels = catalog.grid.cell_pixels;
  const { columns, rows } = parseSize(size);
  const drawn = createWidget({ type, size, settings }, { cellPixels, demoData });

  // The same frame-and-box pair as the display, so the same styles and zooming apply.
  const frame = el("div", "display-frame widget-picture");
  frame.style.setProperty("--display-width", `${columns * cellPixels}px`);
  frame.style.setProperty("--display-height", `${rows * cellPixels}px`);
  setDisplayZoom(frame, zoom);

  const box = el("div", "display widget-picture__box");
  box.style.width = `${columns * cellPixels}px`;
  box.style.height = `${rows * cellPixels}px`;
  drawn.element.style.left = "0";
  drawn.element.style.top = "0";
  box.append(drawn.element);
  frame.append(box);
  return frame;
}
