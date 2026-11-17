// The small button that switches the device page to full screen, which hides the browser's
// address bar on a phone.

import { icon } from "../common/icons.js";

export function setUpFullScreenButton(button) {
  const page = document.documentElement;
  if (!page.requestFullscreen) {
    button.hidden = true;   // this browser cannot do it (an iPhone, for example)
    return;
  }

  button.append(icon("full_screen"));

  button.addEventListener("click", async () => {
    try {
      await page.requestFullscreen();
      // Turning the picture sideways only works on some phones; it is fine if it does not.
      await screen.orientation?.lock?.("landscape").catch(() => {});
    } catch {
      // The browser said no. The page works the same without full screen.
    }
  });

  document.addEventListener("fullscreenchange", () => {
    button.hidden = document.fullscreenElement !== null;
  });
}
