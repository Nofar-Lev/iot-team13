// Turning a moment in time into the text the clock and the date show.
// The month and day names are written out here (not taken from the browser), so that every
// browser shows the same text, and so that the device can later use the same lists.

const WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

const MINUTES_IN_A_DAY = 24 * 60;
const twoDigits = (number) => String(number).padStart(2, "0");

/**
 * The time a clock widget shows.
 * "Set by hand" is stored as offset_minutes: how far the clock is from the automatic time.
 */
export function timeShownByClock(now, clockSettings) {
  if (clockSettings.time_mode !== "manual") return now;
  return new Date(now.getTime() + clockSettings.offset_minutes * 60_000);
}

/** The pieces of a clock face: { time: "9:05", seconds: "07" or null, period: "AM" or null }. */
export function clockFace(moment, clockSettings) {
  const hours = moment.getHours();
  const minutes = twoDigits(moment.getMinutes());
  const seconds = clockSettings.show_seconds ? twoDigits(moment.getSeconds()) : null;

  if (clockSettings.format === "12h") {
    const hoursOnDial = hours % 12 === 0 ? 12 : hours % 12;
    return { time: `${hoursOnDial}:${minutes}`, seconds, period: hours < 12 ? "AM" : "PM" };
  }
  return { time: `${twoDigits(hours)}:${minutes}`, seconds, period: null };
}

/** The date in its two forms: "Sun 15 Nov", or "Sunday" above "15 November". */
export function dateText(moment, style) {
  const weekday = WEEKDAYS[moment.getDay()];
  const month = MONTHS[moment.getMonth()];
  const day = moment.getDate();
  if (style === "long") return { weekday, dayAndMonth: `${day} ${month}` };
  return { line: `${weekday.slice(0, 3)} ${day} ${month.slice(0, 3)}` };
}

/** "14:30", chosen by the user at this moment -> the offset_minutes to store. */
export function offsetForChosenTime(now, chosenTime) {
  const [chosenHours, chosenMinutes] = chosenTime.split(":").map(Number);
  const chosen = chosenHours * 60 + chosenMinutes;
  const actual = now.getHours() * 60 + now.getMinutes();
  // The shortest way round the clock: between 12 hours back and 12 hours ahead.
  let offset = (chosen - actual) % MINUTES_IN_A_DAY;
  if (offset > MINUTES_IN_A_DAY / 2) offset -= MINUTES_IN_A_DAY;
  if (offset <= -MINUTES_IN_A_DAY / 2) offset += MINUTES_IN_A_DAY;
  return offset;
}

/** The other way round: the "HH:MM" that a clock with this offset shows at this moment. */
export function chosenTimeForOffset(now, offsetMinutes) {
  const shown = new Date(now.getTime() + offsetMinutes * 60_000);
  return `${twoDigits(shown.getHours())}:${twoDigits(shown.getMinutes())}`;
}
