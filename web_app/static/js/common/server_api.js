// Talking to the server: reading the catalog, the example data and the saved layout.
//
// Saving is the editors' business, and goes through the editing session (../editing/).

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
