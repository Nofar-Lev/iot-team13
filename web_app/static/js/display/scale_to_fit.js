// Zooming the display to fit the room a page gives it.
//
// The display is always 480x320 units inside. The frame around it sets one number, the zoom
// factor, and the styles enlarge or shrink the whole display by it.

/** Show the display at a fixed zoom: 1 is 480x320 page pixels, 0.5 is half of that. */
export function setDisplayZoom(frame, zoom) {
  frame.style.setProperty("--display-zoom", String(zoom));
}

/**
 * Keep the display as large as fits inside `room`, also when the window is resized.
 *
 * unitsWide, unitsHigh:  the display's own size (480 and 320).
 * margin:                page pixels to leave free on each side.
 * largestZoom:           never zoom in beyond this.
 * useHeight:             false for a room whose height follows its content; then only the
 *                        width decides.
 * Returns a function that stops watching.
 */
export function keepDisplayFitted(frame, room, {
  unitsWide = 480, unitsHigh = 320, margin = 0, largestZoom = Infinity, useHeight = true,
} = {}) {
  function fit() {
    const widthZoom = (room.clientWidth - 2 * margin) / unitsWide;
    const heightZoom = useHeight ? (room.clientHeight - 2 * margin) / unitsHigh : Infinity;
    const zoom = Math.max(0.1, Math.min(widthZoom, heightZoom, largestZoom));
    setDisplayZoom(frame, zoom);
  }

  const watcher = new ResizeObserver(fit);
  watcher.observe(room);
  fit();
  return () => watcher.disconnect();
}
