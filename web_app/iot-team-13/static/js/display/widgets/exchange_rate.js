// An exchange rate. Size 2x1. Settings: from which currency, to which currency.
// The rates are example values for now.

import { el } from "../../common/dom.js";
import { icon } from "../../common/icons.js";
import { exchangeRate } from "../units.js";

export function buildExchangeRate(body, { settings, demoData }) {
  const rate = exchangeRate(demoData.exchange_rates_to_usd, settings.from, settings.to);

  const pair = el("div", "exchange__pair");
  pair.append(el("span", "", settings.from), icon("arrow_right"), el("span", "", settings.to));

  const card = el("div", "exchange");
  card.append(pair, el("div", "exchange__rate", rate.toFixed(2)));
  body.append(card);
}
