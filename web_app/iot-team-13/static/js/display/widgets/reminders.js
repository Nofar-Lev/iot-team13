// Today's reminders, each marked done, missed or waiting. Size 4x2. No settings.
// The list is an example for now.

import { el } from "../../common/dom.js";
import { icon } from "../../common/icons.js";

// How many rows fit in the widget.
const MOST_ROWS = 5;

export function buildReminders(body, { demoData }) {
  const reminders = demoData.reminders;
  const doneCount = reminders.filter((reminder) => reminder.status === "done").length;

  const header = el("div", "reminders__header");
  header.append(
    el("span", "reminders__title", "Today"),
    el("span", "reminders__count", `${doneCount} of ${reminders.length} done`),
  );

  const list = el("div", "reminders__list");
  for (const reminder of reminders.slice(0, MOST_ROWS)) {
    const row = el("div", `reminders__row reminders__row--${reminder.status}`);
    row.append(
      icon(`reminder_${reminder.status}`),
      el("span", "reminders__time", reminder.time),
      el("span", "reminders__text", reminder.text),
    );
    list.append(row);
  }

  const card = el("div", "reminders");
  card.append(header, list);
  body.append(card);
}
