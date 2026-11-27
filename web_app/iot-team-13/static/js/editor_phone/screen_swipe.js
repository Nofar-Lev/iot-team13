// A sideways swipe on the preview moves to the next or the previous screen, as on the device.
//
// This file is the rule, with no page elements, so that it is easy to test.
// preview_touches.js listens to the preview and uses it.

// A finger must travel this far sideways (in page units) to count as a swipe.
export const SHORTEST_SWIPE = 40;

/**
 * What a finger's movement asks for: +1 for the next screen, -1 for the previous one, 0 for
 * neither. start and end are { x, y }, where the finger went down and where it came up.
 */
export function screenStepOfSwipe(start, end) {
  const movedX = end.x - start.x;
  const movedY = end.y - start.y;
  const isSwipe = Math.abs(movedX) >= SHORTEST_SWIPE && Math.abs(movedX) > Math.abs(movedY);
  if (!isSwipe) return 0;
  // Swiping to the left pulls the next screen in, as on a phone.
  return movedX < 0 ? +1 : -1;
}
