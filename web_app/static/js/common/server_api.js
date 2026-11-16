// Talking to the server: reading the catalog, the example data and the layout, and saving.

async function readJson(address) {
  const answer = await fetch(address, { cache: "no-store" });
  if (!answer.ok) throw new Error(`The server answered ${answer.status} for ${address}`);
  return answer.json();
}

/** Every widget type, its sizes and settings; the grid; the backgrounds. */
export const fetchCatalog = () => readJson("/api/catalog");

/** Example values for the widgets that have no real data source yet. */
export const fetchDemoData = () => readJson("/api/demo-data");

/** The saved layout: { revision, saved_at, layout }. */
export const fetchSavedLayout = () => readJson("/api/layout");

/**
 * Save a layout.
 * Answers { saved: true, revision, saved_at } or { saved: false, problems: [...] }.
 * Throws if the server cannot be reached at all.
 */
export async function saveLayout(layout) {
  const answer = await fetch("/api/layout", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(layout),
  });
  const details = await answer.json().catch(() => ({}));
  if (answer.ok) return { saved: true, revision: details.revision, saved_at: details.saved_at };
  return { saved: false, problems: details.errors ?? [`The server answered ${answer.status}.`] };
}
