// The SAMPLE parts of the home page: today's reminders, the "add reminder" button, and the box
// for typing or saying a reminder.
//
// Nothing here works yet. The sections show what the finished app will have, with example
// data from data/demo_data.json. Each is marked "Sample" on the page, and pressing one of
// their buttons says so too.

import { el } from "../common/dom.js";
import { icon } from "../common/icons.js";
import { showToast } from "../common/toast.js";

const STATE_WORDS = { done: "Done", missed: "Missed", waiting: "Waiting" };

function sayItIsASample() {
  showToast("This part is a sample. It is not built yet.");
}

export function setUpSampleSections({ demoData }) {
  // --- Today's reminders ----------------------------------------------------------------------

  const reminders = demoData.reminders;
  const doneCount = reminders.filter((reminder) => reminder.status === "done").length;
  document.getElementById("reminders-summary").textContent =
    `${doneCount} of ${reminders.length} done so far`;

  const list = document.getElementById("reminder-list");
  for (const reminder of reminders) {
    const row = el("li", `reminder reminder--${reminder.status}`);
    row.append(
      icon(`reminder_${reminder.status}`),
      el("span", "reminder__time", reminder.time),
      el("span", "reminder__text", reminder.text),
      el("span", "reminder__state", STATE_WORDS[reminder.status] ?? reminder.status),
    );
    list.append(row);
  }

  const addButton = document.getElementById("add-reminder-button");
  addButton.prepend(icon("plus"));
  addButton.addEventListener("click", sayItIsASample);

  // --- Typing or saying a reminder ------------------------------------------------------------

  const microphoneButton = document.getElementById("microphone-button");
  microphoneButton.append(icon("microphone"));
  microphoneButton.addEventListener("click", sayItIsASample);

  document.getElementById("assistant-send-button").addEventListener("click", sayItIsASample);
  document.getElementById("assistant-input").addEventListener("keydown", (event) => {
    if (event.key === "Enter") sayItIsASample();
  });
}
