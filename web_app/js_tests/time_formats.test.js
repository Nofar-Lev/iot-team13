// Tests for the text the clock and the date show, and for the small conversions.
// Run with:  node --test js_tests/

import assert from "node:assert/strict";
import { test } from "node:test";

import {
  chosenTimeForOffset, clockFace, dateText, offsetForChosenTime, timeShownByClock,
} from "../static/js/display/time_formats.js";
import { exchangeRate, temperatureText } from "../static/js/display/units.js";
import { describeSavedTime } from "../static/js/home/saved_time.js";

// Months count from 0 in JavaScript: 10 is November.
const at = (hours, minutes, seconds = 0) => new Date(2026, 10, 15, hours, minutes, seconds);

const settings = (changes = {}) => ({
  format: "24h", show_seconds: false, time_mode: "automatic", offset_minutes: 0, ...changes,
});

test("a 24 hour clock keeps the leading zero", () => {
  assert.deepEqual(clockFace(at(9, 5), settings()), { time: "09:05", seconds: null, period: null });
  assert.deepEqual(clockFace(at(0, 0), settings()), { time: "00:00", seconds: null, period: null });
  assert.equal(clockFace(at(23, 59), settings()).time, "23:59");
});

test("a 12 hour clock says AM or PM and has no hour zero", () => {
  const twelveHours = settings({ format: "12h" });
  assert.deepEqual(clockFace(at(0, 30), twelveHours), { time: "12:30", seconds: null, period: "AM" });
  assert.deepEqual(clockFace(at(9, 5), twelveHours), { time: "9:05", seconds: null, period: "AM" });
  assert.deepEqual(clockFace(at(12, 0), twelveHours), { time: "12:00", seconds: null, period: "PM" });
  assert.deepEqual(clockFace(at(23, 59), twelveHours), { time: "11:59", seconds: null, period: "PM" });
});

test("seconds are shown only when asked for", () => {
  assert.equal(clockFace(at(9, 5, 7), settings()).seconds, null);
  assert.equal(clockFace(at(9, 5, 7), settings({ show_seconds: true })).seconds, "07");
});

test("an automatic clock ignores the offset", () => {
  const now = at(9, 5);
  assert.equal(timeShownByClock(now, settings({ offset_minutes: 90 })).getTime(), now.getTime());
});

test("a clock set by hand runs ahead or behind by its offset", () => {
  const ahead = timeShownByClock(at(9, 5), settings({ time_mode: "manual", offset_minutes: 90 }));
  assert.equal(clockFace(ahead, settings()).time, "10:35");
  const behind = timeShownByClock(at(0, 10), settings({ time_mode: "manual", offset_minutes: -30 }));
  assert.equal(clockFace(behind, settings()).time, "23:40");
});

test("the date has a short and a long form", () => {
  assert.deepEqual(dateText(at(9, 5), "short"), { line: "Sun 15 Nov" });
  assert.deepEqual(dateText(at(9, 5), "long"), { weekday: "Sunday", dayAndMonth: "15 November" });
});

test("choosing a time stores the difference from the real time", () => {
  assert.equal(offsetForChosenTime(at(9, 5), "09:05"), 0);
  assert.equal(offsetForChosenTime(at(9, 5), "10:35"), 90);
  assert.equal(offsetForChosenTime(at(9, 5), "08:00"), -65);
});

test("the difference goes the short way round the clock", () => {
  assert.equal(offsetForChosenTime(at(23, 50), "00:10"), 20);
  assert.equal(offsetForChosenTime(at(0, 10), "23:50"), -20);
  assert.equal(offsetForChosenTime(at(6, 0), "18:00"), 720);
});

test("the stored difference always fits what the server allows", () => {
  for (let hour = 0; hour < 24; hour += 1) {
    for (const chosen of ["00:00", "06:30", "12:00", "17:45", "23:59"]) {
      const offset = offsetForChosenTime(at(hour, 17), chosen);
      assert.ok(Number.isInteger(offset) && offset > -720 && offset <= 720, `${hour}:17 -> ${chosen}`);
    }
  }
});

test("a stored difference turns back into the chosen time", () => {
  for (const chosen of ["00:00", "06:30", "12:00", "17:45", "23:59"]) {
    const now = at(21, 40);
    assert.equal(chosenTimeForOffset(now, offsetForChosenTime(now, chosen)), chosen);
  }
});

test("temperatures are shown in the chosen units", () => {
  assert.equal(temperatureText(23, "celsius"), "23°");
  assert.equal(temperatureText(23, "fahrenheit"), "73°");
  assert.equal(temperatureText(24.5, "celsius", 1), "24.5°");
  assert.equal(temperatureText(24.5, "fahrenheit", 1), "76.1°");
  assert.equal(temperatureText(0, "fahrenheit"), "32°");
});

test("an exchange rate is worked out through the US dollar", () => {
  const valueInUsd = { USD: 1.0, EUR: 1.08, ILS: 0.27 };
  assert.equal(exchangeRate(valueInUsd, "USD", "ILS").toFixed(2), "3.70");
  assert.equal(exchangeRate(valueInUsd, "EUR", "ILS").toFixed(2), "4.00");
  assert.equal(exchangeRate(valueInUsd, "USD", "USD"), 1);
});

test("the saved time is said in words", () => {
  const now = new Date(2026, 10, 15, 18, 0);
  const asServerText = (date) => date.toISOString();
  assert.match(describeSavedTime(null, now), /Nothing was saved yet/);
  assert.equal(describeSavedTime(asServerText(new Date(2026, 10, 15, 14, 32)), now), "Layout saved today at 14:32");
  assert.equal(describeSavedTime(asServerText(new Date(2026, 10, 14, 9, 5)), now), "Layout saved yesterday at 09:05");
  assert.equal(describeSavedTime(asServerText(new Date(2026, 9, 3, 9, 5)), now), "Layout saved on 3 Oct at 09:05");
});
