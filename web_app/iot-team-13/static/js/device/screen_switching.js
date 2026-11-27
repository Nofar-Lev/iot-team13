// Moving between screens on the device page: swipe left or right, tap near the left or right
// edge of the display, or press the arrow keys.

// A finger must travel this far sideways (in page pixels) to count as a swipe.
const SHORTEST_SWIPE = 40;
// A touch that moved less than this is a tap.
const LONGEST_TAP_MOVE = 10;
// A tap this close to the display's left or right edge (as a share of its width) switches screen.
const EDGE_SHARE = 0.2;

/**
 * stage:    the element that receives the touches (the whole page).
 * display:  the display's frame, used to tell where its edges are.
 */
export function watchForScreenSwitching(stage, display, { onPrevious, onNext }) {
  let touchStart = null;

  stage.addEventListener("pointerdown", (event) => {
    touchStart = { x: event.clientX, y: event.clientY };
  });

  stage.addEventListener("pointerup", (event) => {
    if (!touchStart) return;
    const movedX = event.clientX - touchStart.x;
    const movedY = event.clientY - touchStart.y;
    touchStart = null;

    const isSwipe = Math.abs(movedX) >= SHORTEST_SWIPE && Math.abs(movedX) > Math.abs(movedY);
    if (isSwipe) {
      // Swiping to the left pulls the next screen in, as on a phone.
      if (movedX < 0) onNext();
      else onPrevious();
      return;
    }

    const isTap = Math.abs(movedX) < LONGEST_TAP_MOVE && Math.abs(movedY) < LONGEST_TAP_MOVE;
    if (!isTap) return;
    const box = display.getBoundingClientRect();
    if (event.clientY < box.top || event.clientY > box.bottom) return;
    const share = (event.clientX - box.left) / box.width;
    if (share >= 0 && share < EDGE_SHARE) onPrevious();
    if (share <= 1 && share > 1 - EDGE_SHARE) onNext();
  });

  stage.addEventListener("pointercancel", () => {
    touchStart = null;
  });

  window.addEventListener("keydown", (event) => {
    if (event.key === "ArrowLeft") onPrevious();
    if (event.key === "ArrowRight") onNext();
  });
}
