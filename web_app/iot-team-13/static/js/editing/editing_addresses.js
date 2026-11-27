// Talking to the server's editing addresses (server/editing_api.py): becoming the editor in
// use, keeping the draft up to date, saving, discarding, and taking over.
//
// Every request says which editor is asking: the id the server gave this page when its live
// channel connected.

/**
 * Ask the server for one thing, for example askEditingServer("enter", editorId).
 *
 * Answers { ok: true, answer } when the server did it, and otherwise
 * { ok: false, status, reason, problems }: `reason` is the server's short name for why it
 * refused (for example "not_the_editor_in_use"), and `problems` is a list of sentences.
 * Throws if the server cannot be reached at all.
 */
export async function askEditingServer(address, editorId, more = {}, method = "POST") {
  const response = await fetch(`/api/editing/${address}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ editor: editorId, ...more }),
    // Let a request that was just sent still reach the server if the page is closed right after.
    keepalive: true,
  });
  const details = await response.json().catch(() => ({}));
  if (response.ok) return { ok: true, answer: details };
  return {
    ok: false,
    status: response.status,
    reason: details.reason ?? null,
    problems: details.errors ?? [`The server answered ${response.status}.`],
  };
}

/**
 * Tell the server that this editor page is going away. Meant for the moment the page closes,
 * when an ordinary request would be cut off: the browser sends this one on its own time.
 */
export function tellServerThisEditorIsLeaving(editorId) {
  navigator.sendBeacon("/api/editing/leave", JSON.stringify({ editor: editorId }));
}
