// One row of a list that widgets are chosen from: a small picture, a name and a short note.
// Used by the list of widgets and by the list of a widget's sizes.

import { el } from "../common/dom.js";
import { parseSize } from "../common/grid.js";
import { showToast } from "../common/toast.js";
import { defaultSettings } from "../editing/editor_state.js";
import { createWidgetPicture } from "../editing/widget_picture.js";

// Every picture in a row is this many page units high, whatever the widget's size.
const PICTURE_HEIGHT = 40;

/** "4x2" -> "4 × 2" */
export const sizeAsText = (size) => size.replace("x", " × ");

/**
 * catalogWidget, size: the widget and the size the picture shows.
 * name, note:          the row's two lines of text.
 * hasRoom:             false greys the row out. A tap on it then only says why.
 * onChoose():          called when a row that has room is tapped.
 */
export function widgetRow({ catalog, demoData, catalogWidget, size, name, note, hasRoom, onChoose }) {
  const { rows } = parseSize(size);
  const picture = createWidgetPicture(
    { type: catalogWidget.type, size, settings: defaultSettings(catalogWidget) },
    { catalog, demoData, zoom: PICTURE_HEIGHT / (rows * catalog.grid.cell_pixels) },
  );

  const text = el("span", "widget-row__text");
  text.append(el("span", "widget-row__name", name), el("span", "widget-row__note", hasRoom ? note : "No room"));

  const row = el("button", `widget-row${hasRoom ? "" : " widget-row--no-room"}`);
  row.type = "button";
  row.dataset.widgetType = catalogWidget.type;
  row.dataset.widgetSize = size;
  // Not "disabled": a greyed-out row still answers a tap, with a message.
  row.setAttribute("aria-disabled", String(!hasRoom));
  row.append(picture, text);

  row.addEventListener("click", () => {
    if (hasRoom) onChoose();
    else showToast("This screen has no room for that widget.", "problem");
  });
  return row;
}
