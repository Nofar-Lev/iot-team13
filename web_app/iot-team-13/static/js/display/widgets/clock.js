// The clock: floating digits with nothing behind them.
// Sizes: 2x1 (small) and 4x2 (large). Settings: 12 or 24 hours, seconds, time set by hand.

import { el } from "../../common/dom.js";
import { clockFace, timeShownByClock } from "../time_formats.js";

export function buildClock(body, { settings }) {
  const time = el("span", "clock__time");
  // Seconds and AM/PM sit in a narrow column beside the digits.
  const side = el("span", "clock__side");
  const period = el("span", "clock__period");
  const seconds = el("span", "clock__seconds");
  side.append(period, seconds);

  const clock = el("div", "clock");
  clock.append(time, side);
  body.append(clock);

  return function update(now) {
    const face = clockFace(timeShownByClock(now, settings), settings);
    time.textContent = face.time;
    period.textContent = face.period ?? "";
    seconds.textContent = face.seconds ?? "";
    side.hidden = face.period === null && face.seconds === null;
    clock.classList.toggle("clock--with-side", !side.hidden);
  };
}
