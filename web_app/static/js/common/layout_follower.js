// Keeping a page's copy of the layout up to date.
//
// The live channel only says "the layout now has revision 12". This helper compares that with
// the revision the page has, fetches the layout when the page is behind, and makes sure that
// news arriving in the middle of a fetch is not lost.

import { fetchSavedLayout } from "./server_api.js";

/**
 * onLayout(saved): called with { revision, saved_at, layout } every time a newer layout arrives.
 * Returns catchUpWith(revision): call it with every revision number the server mentions.
 */
export function createLayoutFollower({ onLayout }) {
  let revisionWeHave = null;
  let newestRevisionWeHeardOf = null;
  let isFetching = false;

  return async function catchUpWith(serverRevision) {
    newestRevisionWeHeardOf = serverRevision;
    if (isFetching) return;   // the fetch in progress will notice the new number when it ends

    isFetching = true;
    try {
      while (revisionWeHave !== newestRevisionWeHeardOf) {
        const saved = await fetchSavedLayout();
        revisionWeHave = saved.revision;
        // The server may already be past the number we were told about.
        if (saved.revision > newestRevisionWeHeardOf) newestRevisionWeHeardOf = saved.revision;
        onLayout(saved);
      }
    } catch {
      // The server went away in the middle. The page keeps what it has; when the connection
      // returns, the server's "hello" brings us back here.
    } finally {
      isFetching = false;
    }
  };
}
