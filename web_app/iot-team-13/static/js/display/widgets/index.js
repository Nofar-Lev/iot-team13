// Every widget type the display can draw, and how each one looks.
//
// To add a widget: describe it in data/widget_catalog.json, write its drawing file in this
// folder, and add one line here.
//
// A drawing function gets the widget's empty box and { size, settings, demoData }, and fills
// the box. If the widget changes with time (the clock), it returns a function update(now) that
// the display calls every second.

import { el } from "../../common/dom.js";
import { parseSize } from "../../common/grid.js";
import { buildClock } from "./clock.js";
import { buildDate } from "./date.js";
import { buildExchangeRate } from "./exchange_rate.js";
import { buildReminders } from "./reminders.js";
import { buildRoomClimate } from "./room_climate.js";
import { buildStock } from "./stock.js";
import { buildWeather } from "./weather.js";

// look: "card" sits on a soft see-through panel; "floating" is drawn straight on the background.
const WIDGET_DRAWINGS = {
  clock: { build: buildClock, look: "floating" },
  date: { build: buildDate, look: "floating" },
  weather: { build: buildWeather, look: "card" },
  stock: { build: buildStock, look: "card" },
  exchange_rate: { build: buildExchangeRate, look: "card" },
  room_climate: { build: buildRoomClimate, look: "card" },
  reminders: { build: buildReminders, look: "card" },
};

/**
 * Draw one widget.
 * widget:  { type, size, settings } as in the layout.
 * Returns { element, update }. element is as large as the widget's cells; update(now) is
 * null for widgets that never change by themselves.
 */
export function createWidget(widget, { cellPixels, demoData }) {
  const drawing = WIDGET_DRAWINGS[widget.type];
  const { columns, rows } = parseSize(widget.size);

  const element = el("div", `widget widget--${widget.type} widget--${widget.size}`);
  element.style.width = `${columns * cellPixels}px`;
  element.style.height = `${rows * cellPixels}px`;

  const body = el("div", `widget__body widget__body--${drawing ? drawing.look : "card"}`);
  element.append(body);

  if (!drawing) {
    // A layout may name a widget this page does not know yet. Show that plainly.
    body.append(el("div", "widget__unknown", widget.type));
    return { element, update: null };
  }

  const update = drawing.build(body, { size: widget.size, settings: widget.settings, demoData }) ?? null;
  if (update) update(new Date());
  return { element, update };
}
