// Selecting by a tap on the preview's side of the screen.
//
//   A tap on a widget selects it.
//   A tap anywhere else (an empty place of the preview, or the space around it) lets go of
//   the selected widget.
//
// The panel is not part of this: a tap there never changes what is selected.

// A finger that travelled further than this between going down and coming up was not tapping.
const LONGEST_TAP_MOVE = 10;

/**
 * stage:        the element that holds the preview and the space around it.
 * previewFrame: the preview's picture, to tell its widgets from anything else.
 * onTapOutside(): called for a tap that is not on a widget.
 */
export function setUpSelectionByTap({ stage, previewFrame, state, onTapOutside }) {
  let wentDownAt = null;

  stage.addEventListener("pointerdown", (event) => {
    wentDownAt = { x: event.clientX, y: event.clientY };
  });

  stage.addEventListener("click", (event) => {
    // The arrows on the preview's edges have their own work.
    if (event.target.closest(".preview__arrow")) return;

    // A swipe made with a mouse also ends in a "click". It is not a tap.
    const moved = wentDownAt ? Math.hypot(event.clientX - wentDownAt.x, event.clientY - wentDownAt.y) : 0;
    wentDownAt = null;
    if (moved > LONGEST_TAP_MOVE) return;

    const widgetElement = event.target.closest(".widget");
    if (widgetElement && previewFrame.contains(widgetElement)) {
      state.selectWidget(Number(widgetElement.dataset.widgetIndex));
    } else {
      onTapOutside();
    }
  });
}
