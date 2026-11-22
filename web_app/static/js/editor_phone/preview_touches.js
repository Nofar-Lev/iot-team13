// What a touch on the preview means.
//
//   A short tap on a widget        selects it.
//   A short tap on an empty place  lets go of the selected widget.
//   A sideways swipe               moves to the next or the previous screen, wherever it starts.
//   Press and hold on a widget     lifts it; it then follows the finger and is dropped where
//                                  the finger is lifted. It is selected from the moment it
//                                  lifts, and stays selected after the drop.
//
// The three cannot be mistaken for one another: a tap is short and still, a swipe moves at
// once, and a hold stays put first.

import { watchPresses } from "./press_and_hold.js";
import { screenStepOfSwipe } from "./screen_swipe.js";

// A finger that travelled further than this between going down and coming up was not tapping.
const LONGEST_TAP_MOVE = 10;

/**
 * state:        the editor's state (editing/editor_state.js).
 * displayView:  the preview (display/display_view.js).
 * carrying:     what is shown while a widget is carried (carrying.js).
 * onTapOutside(): a tap on the preview that is not on a widget.
 */
export function setUpPreviewTouches({ state, displayView, carrying, onTapOutside }) {
  const frame = displayView.frame;
  let held = null;   // the widget being carried: { index, element }

  const widgetUnder = (event) => {
    const element = event.target.closest?.(".widget");
    return element && displayView.display.contains(element) ? element : null;
  };

  // Every movement of a finger on the preview is the page's to read. Saying so here, and not
  // only in the styles, also stops the browser from reading a swipe as the start of a "fling":
  // after a fling it would swallow the next tap, wherever that tap lands.
  frame.addEventListener("touchmove", (event) => {
    if (event.cancelable) event.preventDefault();
  }, { passive: false });

  function letGoOfTheHeldWidget() {
    held.element.classList.remove("widget--being-moved");
    held = null;
  }

  watchPresses(frame, {
    mayHold: (event) => widgetUnder(event) !== null,

    onHoldStart(event) {
      const element = widgetUnder(event);
      const index = Number(element.dataset.widgetIndex);
      const widget = state.currentScreen().widgets[index];
      held = { index, element };

      // Selected from the moment it lifts, so the panel shows its options while it is carried.
      state.selectWidget(index);
      element.classList.add("widget--being-moved");

      const box = displayView.display.getBoundingClientRect();
      const fingerCol = ((event.clientX - box.left) / box.width) * state.grid.columns;
      const fingerRow = ((event.clientY - box.top) / box.height) * state.grid.rows;
      const picture = element.cloneNode(true);
      picture.classList.remove("widget--selected", "widget--being-moved");
      picture.style.left = "0";
      picture.style.top = "0";

      carrying.start({
        size: widget.size,
        grabbedAt: { x: fingerCol - widget.col, y: fingerRow - widget.row },
        movingIndex: index,
        picture,
      }, event);
    },

    onHoldMove: (event) => carrying.moveTo(event),

    onHoldEnd() {
      const { index } = held;
      const place = carrying.end();
      letGoOfTheHeldWidget();
      if (place) state.moveWidget(index, place.col, place.row);
    },

    onHoldCancel() {
      carrying.cancel();
      letGoOfTheHeldWidget();
    },

    onShortPress(start, end, event) {
      const step = screenStepOfSwipe(start, end);
      if (step !== 0) {
        state.showScreen(state.screenIndex() + step);
        return;
      }
      if (Math.hypot(end.x - start.x, end.y - start.y) > LONGEST_TAP_MOVE) return;   // neither a tap nor a swipe

      const element = widgetUnder(event);
      if (element) state.selectWidget(Number(element.dataset.widgetIndex));
      else onTapOutside();
    },
  });
}
