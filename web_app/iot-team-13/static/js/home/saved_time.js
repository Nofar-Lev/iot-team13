// Saying when the layout was last saved, in words.

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const twoDigits = (number) => String(number).padStart(2, "0");

const isSameDay = (first, second) =>
  first.getFullYear() === second.getFullYear() &&
  first.getMonth() === second.getMonth() &&
  first.getDate() === second.getDate();

/**
 * savedAt: when the layout was saved, as the server gives it (text in UTC), or null if the
 *          display still shows the layout it started with.
 * now:     the current moment.
 */
export function describeSavedTime(savedAt, now) {
  if (savedAt === null) return "Showing the starting layout. Nothing was saved yet.";

  const saved = new Date(savedAt);
  const time = `${twoDigits(saved.getHours())}:${twoDigits(saved.getMinutes())}`;
  if (isSameDay(saved, now)) return `Layout saved today at ${time}`;

  const yesterday = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
  if (isSameDay(saved, yesterday)) return `Layout saved yesterday at ${time}`;
  return `Layout saved on ${saved.getDate()} ${MONTHS[saved.getMonth()]} at ${time}`;
}
