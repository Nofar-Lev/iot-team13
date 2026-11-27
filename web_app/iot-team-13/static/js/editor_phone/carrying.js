// What is shown while a widget is carried, and where it may land.
//
// Used for both kinds of carrying: moving a widget that is on the preview, and bringing a new
// one in from the panel's list. While something is carried:
//   - the grid gets brighter;
//   - a "ghost" of the widget shows the cells it would take. It snaps to the grid: green
//     where the widget fits, red where it would overlap another widget;
//   - a new widget that is still outside the preview is shown as a small picture under the
//     finger.

import { el } from "../common/dom.js";
import { parseSize, snapToGrid } from "../common/grid.js";

// A finger still counts as "over the preview" this far outside its edge, in cells.
const SLACK_AROUND_PREVIEW = 0.5;

/**
 * state:       the editor's state (editing/editor_state.js).
 * displayView: the preview (display/display_view.js).
 */
export function createCarrying({ state, displayView }) {
  const display = displayView.display;
  const grid = state.grid;

  const ghost = el("div", "carry-ghost");
  ghost.hidden = true;
  displayView.overlay.append(ghost);

  let carried = null;   // what is being carried, or null

  function fingerInCells(event) {
    const box = display.getBoundingClientRect();
    return {
      x: ((event.clientX - box.left) / box.width) * grid.columns,
      y: ((event.clientY - box.top) / box.height) * grid.rows,
    };
  }

  function isOverPreview(cells) {
    return (
      cells.x >= -SLACK_AROUND_PREVIEW && cells.x <= grid.columns + SLACK_AROUND_PREVIEW &&
      cells.y >= -SLACK_AROUND_PREVIEW && cells.y <= grid.rows + SLACK_AROUND_PREVIEW
    );
  }

  function showGhostAt(place, fits) {
    const { columns, rows } = parseSize(carried.size);
    ghost.style.left = `${(place.col / grid.columns) * 100}%`;
    ghost.style.top = `${(place.row / grid.rows) * 100}%`;
    ghost.style.width = `${(columns / grid.columns) * 100}%`;
    ghost.style.height = `${(rows / grid.rows) * 100}%`;
    ghost.classList.toggle("carry-ghost--fits", fits);
    ghost.classList.toggle("carry-ghost--blocked", !fits);
    ghost.dataset.col = String(place.col);
    ghost.dataset.row = String(place.row);
    ghost.hidden = false;
  }

  function putDown() {
    if (carried.floating) carried.floating.remove();
    ghost.hidden = true;
    ghost.replaceChildren();
    display.classList.remove("display--carrying");
    document.body.classList.remove("is-carrying");
    carried = null;
  }

  return {
    isCarrying: () => carried !== null,

    /**
     * size:        the carried widget's size.
     * grabbedAt:   where in the widget the finger holds it, in cells from its top left corner.
     * movingIndex: the widget's index on the screen, or -1 for a new widget.
     * picture:     the element shown inside the ghost.
     * floating:    an element that follows the finger while it is outside the preview, or null.
     * event:       where the finger is now.
     */
    start({ size, grabbedAt, movingIndex, picture, floating = null }, event) {
      carried = { size, grabbedAt, movingIndex, floating, place: null, fits: false };
      ghost.replaceChildren(picture);
      display.classList.add("display--carrying");
      document.body.classList.add("is-carrying");
      if (floating) document.body.append(floating);
      this.moveTo(event);
    },

    moveTo(event) {
      if (!carried) return;
      const cells = fingerInCells(event);
      if (isOverPreview(cells)) {
        carried.place = snapToGrid(grid, carried.size, cells.x - carried.grabbedAt.x, cells.y - carried.grabbedAt.y);
        carried.fits = state.canPlaceWidget(carried.size, carried.place.col, carried.place.row, carried.movingIndex);
        showGhostAt(carried.place, carried.fits);
      } else {
        carried.place = null;
        ghost.hidden = true;
      }
      if (carried.floating) {
        carried.floating.hidden = carried.place !== null;
        carried.floating.style.left = `${event.clientX}px`;
        carried.floating.style.top = `${event.clientY}px`;
      }
    },

    /** The finger was lifted. Answers the place the widget may land on, or null if there is none. */
    end() {
      if (!carried) return null;
      const place = carried.place && carried.fits ? carried.place : null;
      putDown();
      return place;
    },

    /** The carrying was called off. Nothing lands anywhere. */
    cancel() {
      if (carried) putDown();
    },
  };
}
