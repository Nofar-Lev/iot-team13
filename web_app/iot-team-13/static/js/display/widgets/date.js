// The date: floating text. Size 2x1. Setting: short form (one line) or long form (two lines).

import { el } from "../../common/dom.js";
import { dateText } from "../time_formats.js";

export function buildDate(body, { settings }) {
  const date = el("div", `date date--${settings.style}`);
  const firstLine = el("div", "date__first-line");
  const secondLine = el("div", "date__second-line");
  date.append(firstLine, secondLine);
  body.append(date);

  return function update(now) {
    const text = dateText(now, settings.style);
    if (settings.style === "long") {
      firstLine.textContent = text.weekday;
      secondLine.textContent = text.dayAndMonth;
    } else {
      firstLine.textContent = text.line;
      secondLine.textContent = "";
    }
  };
}
