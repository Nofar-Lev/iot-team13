// One stock. Size 2x1. Setting: the symbol.
// The price and the change are example values for now; the symbol is the user's.

import { el } from "../../common/dom.js";
import { icon } from "../../common/icons.js";

export function buildStock(body, { settings, demoData }) {
  const stock = demoData.stock;
  const isUp = stock.change_percent >= 0;

  const change = el("span", `stock__change stock__change--${isUp ? "up" : "down"}`);
  change.append(
    icon(isUp ? "going_up" : "going_down"),
    el("span", "", `${Math.abs(stock.change_percent).toFixed(1)}%`),
  );

  const bottomLine = el("div", "stock__bottom-line");
  bottomLine.append(el("span", "stock__price", stock.price.toFixed(2)), change);

  const card = el("div", "stock");
  card.append(el("div", "stock__symbol", settings.symbol.trim() || "—"), bottomLine);
  body.append(card);
}
