// Dragging widgets: from the list onto the display, and from place to place on the display.
//
// While a widget is dragged, a "ghost" of it shows the cells it would take. The ghost snaps to
// the grid: it is green where the widget fits and red where it would overlap another widget.
// Letting go on green places the widget; letting go on red, or outside the display, changes
// nothing. A press that never turns into a drag counts as a click.
//
// Written with pointer events, so the same code works with a mouse and with a finger.

import { el } from "../common/dom.js";
import { parseSize, snapToGrid } from "../common/grid.js";

// The pointer must move this far (in page pixels) before a press becomes a drag.
const MOVE_THAT_STARTS_A_DRAG = 5;
// A drag still counts as "over the display" this far outside its edge, in cells.
const SLACK_AROUND_DISPLAY = 0.5;

/**
 * state:        the editor's state (editor_state.js).
 * displayView:  the display being edited (display_view.js).
 * createGhostPicture(widget): an element that shows a widget, used as the ghost for a widget
 *               that is not on the display yet.
 */
export function setUpDragging({ state, displayView, createGhostPicture }) {
  const display = displayView.display;
  const grid = state.grid;

  const gridLines = el("div", "grid-lines");
  const ghost = el("div", "drop-ghost");
  ghost.hidden = true;
  displayView.overlay.append(gridLines, ghost);

  let drag = null;   // the press or drag in progress, or null

  // --- Where the pointer is, in cells ---------------------------------------------------------

  function pointerInCells(event) {
    const box = display.getBoundingClientRect();
    return {
      x: ((event.clientX - box.left) / box.width) * grid.columns,
      y: ((event.clientY - box.top) / box.height) * grid.rows,
    };
  }

  function isOverDisplay(cells) {
    return (
      cells.x >= -SLACK_AROUND_DISPLAY && cells.x <= grid.columns + SLACK_AROUND_DISPLAY &&
      cells.y >= -SLACK_AROUND_DISPLAY && cells.y <= grid.rows + SLACK_AROUND_DISPLAY
    );
  }

  // --- The ghost ------------------------------------------------------------------------------

  function showGhostAt(place, fits) {
    const { columns, rows } = parseSize(drag.size);
    ghost.style.left = `${(place.col / grid.columns) * 100}%`;
    ghost.style.top = `${(place.row / grid.rows) * 100}%`;
    ghost.style.width = `${(columns / grid.columns) * 100}%`;
    ghost.style.height = `${(rows / grid.rows) * 100}%`;
    ghost.classList.toggle("drop-ghost--fits", fits);
    ghost.classList.toggle("drop-ghost--blocked", !fits);
    ghost.hidden = false;
  }

  // --- One press, from pointer down to pointer up ---------------------------------------------

  /**
   * size:           the dragged widget's size.
   * grabbedAt:      where in the widget the pointer holds it, in cells from its top left corner.
   * movingIndex:    the widget's index on the screen, or -1 for a new widget.
   * ghostPicture(): the element shown inside the ghost.
   * floating:       an element that follows the pointer while it is outside the display, or null.
   * onDrop(place):  called when the widget is let go on a free place.
   * onClick():      called when the press never became a drag.
   * onDragStart(), onDragEnd(): for the caller's own visual changes.
   */
  function beginPress(event, press) {
    if (drag || event.button > 0) return;
    event.preventDefault();
    drag = { ...press, startX: event.clientX, startY: event.clientY, isDragging: false, place: null, fits: false };
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp);
    window.addEventListener("pointercancel", cancelDrag);
    window.addEventListener("keydown", onKeyDown);
  }

  function onPointerMove(event) {
    if (!drag.isDragging) {
      const moved = Math.hypot(event.clientX - drag.startX, event.clientY - drag.startY);
      if (moved < MOVE_THAT_STARTS_A_DRAG) return;
      drag.isDragging = true;
      ghost.replaceChildren(drag.ghostPicture());
      document.body.classList.add("is-dragging");
      display.classList.add("display--dragging");
      if (drag.floating) document.body.append(drag.floating);
      drag.onDragStart?.();
    }

    const cells = pointerInCells(event);
    if (isOverDisplay(cells)) {
      drag.place = snapToGrid(grid, drag.size, cells.x - drag.grabbedAt.x, cells.y - drag.grabbedAt.y);
      drag.fits = state.canPlaceWidget(drag.size, drag.place.col, drag.place.row, drag.movingIndex);
      showGhostAt(drag.place, drag.fits);
    } else {
      drag.place = null;
      ghost.hidden = true;
    }

    if (drag.floating) {
      drag.floating.hidden = drag.place !== null;
      drag.floating.style.left = `${event.clientX}px`;
      drag.floating.style.top = `${event.clientY}px`;
    }
  }

  function onPointerUp() {
    const finished = drag;
    endPress();
    if (!finished.isDragging) finished.onClick?.();
    else if (finished.place && finished.fits) finished.onDrop(finished.place);
  }

  function onKeyDown(event) {
    if (event.key === "Escape") cancelDrag();
  }

  function cancelDrag() {
    endPress();
  }

  function endPress() {
    window.removeEventListener("pointermove", onPointerMove);
    window.removeEventListener("pointerup", onPointerUp);
    window.removeEventListener("pointercancel", cancelDrag);
    window.removeEventListener("keydown", onKeyDown);
    if (drag.isDragging) drag.onDragEnd?.();
    if (drag.floating) drag.floating.remove();
    ghost.hidden = true;
    ghost.replaceChildren();
    document.body.classList.remove("is-dragging");
    display.classList.remove("display--dragging");
    drag = null;
  }

  // --- The two kinds of press -----------------------------------------------------------------

  /** A press on an entry of the widget list. */
  function pressOnPaletteEntry(event, widget, entryElement) {
    const { columns, rows } = parseSize(widget.size);
    const floating = entryElement.querySelector(".widget-picture").cloneNode(true);
    floating.classList.add("floating-picture");

    beginPress(event, {
      size: widget.size,
      grabbedAt: { x: columns / 2, y: rows / 2 },   // hold a new widget by its middle
      movingIndex: -1,
      ghostPicture: () => createGhostPicture(widget),
      floating,
      onDrop: (place) => state.addWidget(widget.type, widget.size, place.col, place.row),
      onClick: () => pressHandlers.onPaletteClick(widget),
    });
  }

  /** A press on the display: on a widget, or on the empty background. */
  function pressOnDisplay(event) {
    if (event.target.closest(".widget__remove")) return;   // that button handles itself
    const widgetElement = event.target.closest(".widget");
    if (!widgetElement || !display.contains(widgetElement)) {
      state.selectWidget(null);
      return;
    }

    const index = Number(widgetElement.dataset.widgetIndex);
    const widget = state.currentScreen().widgets[index];
    state.selectWidget(index);

    const cells = pointerInCells(event);
    beginPress(event, {
      size: widget.size,
      grabbedAt: { x: cells.x - widget.col, y: cells.y - widget.row },
      movingIndex: index,
      ghostPicture() {
        const copy = widgetElement.cloneNode(true);
        copy.classList.remove("widget--selected");
        copy.querySelector(".widget__remove")?.remove();
        copy.style.left = "0";
        copy.style.top = "0";
        return copy;
      },
      floating: null,
      onDrop: (place) => state.moveWidget(index, place.col, place.row),
      onDragStart: () => widgetElement.classList.add("widget--being-moved"),
      onDragEnd: () => widgetElement.classList.remove("widget--being-moved"),
    });
  }

  display.addEventListener("pointerdown", pressOnDisplay);

  const pressHandlers = {
    pressOnPaletteEntry,
    /** Set by the editor: what a plain click on a list entry does. */
    onPaletteClick: () => {},
  };
  return pressHandlers;
}
