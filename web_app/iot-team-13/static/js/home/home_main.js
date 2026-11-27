// The home page: what the finished app's first page will look like.
//
// Real:    the picture of the display, its connection state, and the Edit button.
// Sample:  the reminders, the "add reminder" button, the box for typing or saying a reminder.

import { fetchCatalog, fetchDemoData } from "../common/server_api.js";
import { showToast } from "../common/toast.js";
import { icon } from "../common/icons.js";
import { setUpDisplayCard } from "./display_card.js";
import { setUpSampleSections } from "./sample_sections.js";

async function startHomePage() {
  const [catalog, demoData] = await Promise.all([fetchCatalog(), fetchDemoData()]);

  setUpDisplayCard({
    catalog,
    demoData,
    preview: document.getElementById("display-preview"),
    screensBar: document.getElementById("display-screens"),
    status: document.getElementById("display-status"),
    savedText: document.getElementById("display-saved"),
  });
  document.getElementById("edit-button").prepend(icon("pencil"));

  setUpSampleSections({ demoData });
  document.body.dataset.ready = "true";
}

startHomePage().catch((problem) => {
  console.error(problem);
  showToast("The page could not start. Is the server running?", "problem");
});
