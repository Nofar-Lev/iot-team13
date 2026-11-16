// The device page: plays the part of the real display.
//
// It draws the saved layout, listens on the live channel, and redraws by itself when a new
// layout is saved. If the server becomes unreachable it keeps showing what it has, the clock
// keeps running, and the connection icon changes. When the server is back it catches up.

import { el } from "../common/dom.js";
import { createLayoutFollower } from "../common/layout_follower.js";
import { openLiveChannel } from "../common/live_channel.js";
import { fetchCatalog, fetchDemoData } from "../common/server_api.js";
import { createDisplayView, preloadBackgrounds } from "../display/display_view.js";
import { keepDisplayFitted } from "../display/scale_to_fit.js";
import { createConnectionIcon } from "./connection_icon.js";
import { setUpFullScreenButton } from "./full_screen.js";
import { createScreenDots } from "./screen_dots.js";
import { watchForScreenSwitching } from "./screen_switching.js";

// Page pixels kept free around the display: the case's edge, plus a little air.
const ROOM_AROUND_DISPLAY = 22;

async function startDevicePage() {
  const stage = document.getElementById("device-stage");
  const deviceBody = document.getElementById("device-body");

  const [catalog, demoData] = await Promise.all([fetchCatalog(), fetchDemoData()]);
  preloadBackgrounds(catalog);

  const display = createDisplayView({ catalog, demoData });
  const connectionIcon = createConnectionIcon();
  const screenDots = createScreenDots();
  display.overlay.append(connectionIcon.element, screenDots.element);
  deviceBody.append(display.frame);
  keepDisplayFitted(display.frame, stage, { margin: ROOM_AROUND_DISPLAY });

  // What the device is showing.
  let layout = null;
  let revision = null;
  let screenIndex = 0;

  function drawCurrentScreen() {
    screenIndex = Math.min(screenIndex, layout.screens.length - 1);
    display.showScreen(layout.screens[screenIndex]);
    screenDots.show(layout.screens.length, screenIndex);
    document.body.dataset.revision = String(revision);
    document.body.dataset.screen = String(screenIndex);
  }

  function switchScreen(step) {
    if (!layout) return;
    const target = screenIndex + step;
    if (target < 0 || target >= layout.screens.length) return;
    screenIndex = target;
    drawCurrentScreen();   // at once, with no sliding, as on the real device
  }

  const catchUpWith = createLayoutFollower({
    onLayout(saved) {
      layout = saved.layout;
      revision = saved.revision;
      drawCurrentScreen();
    },
  });

  openLiveChannel({
    role: "device",
    onNews(name, details) {
      // "hello" arrives on every (re)connection, "layout" on every Save.
      if (name === "hello" || name === "layout") catchUpWith(details.revision);
    },
    onConnectionChange: connectionIcon.show,
  });

  watchForScreenSwitching(stage, display.frame, {
    onPrevious: () => switchScreen(-1),
    onNext: () => switchScreen(+1),
  });
  setUpFullScreenButton(document.getElementById("full-screen-button"));
}

startDevicePage().catch((problem) => {
  console.error(problem);
  document.getElementById("device-body").replaceWith(
    el("p", "device-message", "The device page could not start. Is the server running?"),
  );
});
