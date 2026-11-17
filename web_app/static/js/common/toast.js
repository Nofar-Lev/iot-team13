// A short message that appears at the bottom of the page and goes away by itself.

import { el } from "./dom.js";

const STAYS_FOR_MS = 3500;

let toast = null;
let hideTimer = null;

/** kind: "info", "success" or "problem". */
export function showToast(text, kind = "info") {
  if (!toast) {
    toast = el("div", "toast");
    toast.setAttribute("role", "status");
    document.body.append(toast);
  }
  toast.textContent = text;
  toast.className = `toast toast--${kind} toast--showing`;
  clearTimeout(hideTimer);
  hideTimer = setTimeout(() => toast.classList.remove("toast--showing"), STAYS_FOR_MS);
}
