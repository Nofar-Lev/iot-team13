// The small icon in the display's top right corner: green while the device is connected,
// a warning colour with a line through it while it is not.

import { el } from "../common/dom.js";
import { icon } from "../common/icons.js";

export function createConnectionIcon() {
  const holder = el("div", "connection-icon");

  function show(isConnected) {
    holder.className = `connection-icon connection-icon--${isConnected ? "connected" : "lost"}`;
    holder.dataset.connected = String(isConnected);
    holder.replaceChildren(icon(isConnected ? "connected" : "not_connected"));
  }

  show(false);
  return { element: holder, show };
}
