// Press and hold: telling a finger that stays put from one that taps, swipes or scrolls.
//
// On a touch screen a moving finger already means something (a swipe, a scroll), and a short
// touch is a tap. So "carry this" needs a signal of its own, and the signal is the one phones
// use on their home screens: put the finger down and keep it still for a moment. Then the
// thing lifts, and follows the finger until it is let go.

// How long the finger must stay put before the hold "takes", in milliseconds.
export const HOLD_TIME_MS = 350;
// A finger that travelled further than this (in page units) before that was not holding.
export const STILL_ENOUGH_TO_HOLD = 10;

/**
 * Watch the presses that start on an element.
 *
 * mayHold(event):      may a hold start from this press? (Is the finger on something that can
 *                      be carried?) Where it answers false, every press is a short one.
 * onHoldStart(event):  the finger stayed put long enough. event is the press's first event.
 * onHoldMove(event):   the finger moved while holding.
 * onHoldEnd(event):    the finger was lifted while holding.
 * onHoldCancel():      the browser took the touch away while holding.
 * onShortPress(start, end, event): the finger was lifted without ever holding. start and end
 *                      are { x, y }: where it went down and where it came up. Left out, short
 *                      presses are left to the element's own "click".
 */
export function watchPresses(element, { mayHold, onHoldStart, onHoldMove, onHoldEnd, onHoldCancel, onShortPress }) {
  let press = null;              // the press in progress: { pointerId, start, firstEvent, timer, isHolding }
  let swallowNextClick = false;  // the "click" that a browser sends after a hold is not a tap

  function forget() {
    if (press) clearTimeout(press.timer);
    press = null;
  }

  element.addEventListener("pointerdown", (event) => {
    if (press || event.button > 0) return;
    swallowNextClick = false;
    press = { pointerId: event.pointerId, start: { x: event.clientX, y: event.clientY }, isHolding: false, timer: null };

    if (mayHold(event)) {
      press.timer = setTimeout(() => {
        press.isHolding = true;
        // From here on, every movement of this finger comes to this element, wherever it goes.
        try {
          element.setPointerCapture(press.pointerId);
        } catch {
          // The finger was lifted in the same instant. The pointerup that follows ends the press.
        }
        onHoldStart(event);
      }, HOLD_TIME_MS);
    }
  });

  element.addEventListener("pointermove", (event) => {
    if (!press || event.pointerId !== press.pointerId) return;
    if (press.isHolding) {
      onHoldMove(event);
      return;
    }
    // Moving before the hold took: this is a swipe or a scroll, not a hold.
    const moved = Math.hypot(event.clientX - press.start.x, event.clientY - press.start.y);
    if (moved > STILL_ENOUGH_TO_HOLD) clearTimeout(press.timer);
  });

  element.addEventListener("pointerup", (event) => {
    if (!press || event.pointerId !== press.pointerId) return;
    const { isHolding, start } = press;
    forget();
    if (isHolding) {
      swallowNextClick = true;
      onHoldEnd(event);
    } else if (onShortPress) {
      onShortPress(start, { x: event.clientX, y: event.clientY }, event);
    }
  });

  element.addEventListener("pointercancel", (event) => {
    if (!press || event.pointerId !== press.pointerId) return;
    const { isHolding } = press;
    forget();
    if (isHolding) onHoldCancel();
  });

  // While holding, the finger's movement is ours. Without this a list under the finger would
  // start to scroll, and the browser would take the touch away. (A browser only lets a page
  // say this if the listener is marked as "not passive".)
  element.addEventListener("touchmove", (event) => {
    if (press && press.isHolding && event.cancelable) event.preventDefault();
  }, { passive: false });

  // A long press is also how a browser opens its own menu. Not here.
  element.addEventListener("contextmenu", (event) => event.preventDefault());

  // Listened for on the way down to the element's children, so that it comes first.
  element.addEventListener("click", (event) => {
    if (!swallowNextClick) return;
    swallowNextClick = false;
    event.stopPropagation();
    event.preventDefault();
  }, { capture: true });
}
