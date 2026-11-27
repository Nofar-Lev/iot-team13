// The real part of the home page: a picture of what the display is showing, whether the
// display is connected, and when the layout was last saved.
//
// The picture is drawn by the same module the device uses, from the saved layout. It follows
// the live channel, so it changes by itself when a new layout is saved.

import { el } from "../common/dom.js";
import { icon } from "../common/icons.js";
import { createLayoutFollower } from "../common/layout_follower.js";
import { openLiveChannel } from "../common/live_channel.js";
import { createDisplayView, preloadBackgrounds } from "../display/display_view.js";
import { keepDisplayFitted } from "../display/scale_to_fit.js";
import { describeSavedTime } from "./saved_time.js";

// The preview fills the card's width, up to this zoom.
const LARGEST_ZOOM = 1.4;
// The dark case around the preview, in page pixels on each side.
const CASE_EDGE = 12;

export function setUpDisplayCard({ catalog, demoData, preview, screensBar, status, savedText }) {
  preloadBackgrounds(catalog);
  const display = createDisplayView({ catalog, demoData });
  preview.append(display.frame);
  keepDisplayFitted(display.frame, preview, { margin: CASE_EDGE, largestZoom: LARGEST_ZOOM, useHeight: false });

  let layout = null;
  let screenIndex = 0;

  // --- The picture and the dots under it ------------------------------------------------------

  function arrowButton(iconName, label, step) {
    const button = el("button", "icon-button");
    button.type = "button";
    button.setAttribute("aria-label", label);
    button.append(icon(iconName));
    button.disabled = screenIndex + step < 0 || screenIndex + step >= layout.screens.length;
    button.addEventListener("click", () => showScreen(screenIndex + step));
    return button;
  }

  function showScreen(index) {
    screenIndex = Math.max(0, Math.min(index, layout.screens.length - 1));
    display.showScreen(layout.screens[screenIndex]);

    screensBar.replaceChildren();
    if (layout.screens.length < 2) return;
    const dots = el("div", "display-card__dots");
    layout.screens.forEach((_, dotIndex) => {
      const dot = el("button", `display-card__dot${dotIndex === screenIndex ? " display-card__dot--current" : ""}`);
      dot.type = "button";
      dot.setAttribute("aria-label", `Screen ${dotIndex + 1}`);
      dot.addEventListener("click", () => showScreen(dotIndex));
      dots.append(dot);
    });
    screensBar.append(
      arrowButton("back", "Previous screen", -1),
      dots,
      arrowButton("forward", "Next screen", +1),
    );
  }

  const catchUpWith = createLayoutFollower({
    onLayout(saved) {
      layout = saved.layout;
      showScreen(screenIndex);
      savedText.textContent = describeSavedTime(saved.saved_at, new Date());
      preview.dataset.revision = String(saved.revision);
    },
  });

  // --- Whether the display is connected -------------------------------------------------------

  let serverIsReachable = false;
  let displayIsOnline = false;

  function showStatus() {
    let state = "offline";
    let text = "Display offline";
    let iconName = "not_connected";
    if (!serverIsReachable) {
      state = "no-server";
      text = "No connection to the server";
    } else if (displayIsOnline) {
      state = "online";
      text = "Display online";
      iconName = "connected";
    }
    status.className = `display-status display-status--${state}`;
    status.dataset.state = state;
    status.replaceChildren(icon(iconName), el("span", "", text));
  }

  openLiveChannel({
    role: "home",
    onNews(name, details) {
      if (name === "hello") displayIsOnline = details.display_online;
      if (name === "display") displayIsOnline = details.online;
      if (name === "hello" || name === "layout") catchUpWith(details.revision);
      showStatus();
    },
    onConnectionChange(isConnected) {
      serverIsReachable = isConnected;
      showStatus();
    },
  });
  showStatus();
}
