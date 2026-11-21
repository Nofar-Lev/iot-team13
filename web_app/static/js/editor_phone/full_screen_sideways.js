// Full screen, with the picture held sideways.
//
// A browser lets a page do this only as the answer to a tap, and not every browser lets it at
// all: an iPhone's does neither. So both steps are tried, and neither is required. Where they
// do not happen, the editor still works; the page asks the user to turn the phone.

/**
 * Try to go full screen and to hold the picture sideways. Call it from a tap.
 * Answers true if the page is now in full screen.
 */
export async function enterFullScreenSideways() {
  const page = document.documentElement;
  let isFullScreen = false;
  try {
    if (page.requestFullscreen) {
      await page.requestFullscreen();
      isFullScreen = true;
    }
  } catch {
    // The browser said no. The editor works the same under the browser's bars.
  }
  try {
    // Only allowed while in full screen, and only on some phones.
    await screen.orientation?.lock?.("landscape");
  } catch {
    // The user turns the phone by hand.
  }
  return isFullScreen;
}

/** Call listener() when the page leaves full screen (the phone's Back gesture, for example). */
export function onLeavingFullScreen(listener) {
  document.addEventListener("fullscreenchange", () => {
    if (document.fullscreenElement === null) listener();
  });
}
