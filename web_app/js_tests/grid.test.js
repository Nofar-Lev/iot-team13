// Tests for the grid arithmetic. Run with:  node --test js_tests/

import assert from "node:assert/strict";
import { test } from "node:test";

import {
  areaOf, areasOverlap, canPlace, firstFreePlace, fitsInsideGrid, parseSize, snapToGrid,
} from "../static/js/common/grid.js";

const GRID = { columns: 6, rows: 4 };
const widget = (size, col, row) => ({ type: "clock", size, col, row, settings: {} });

test("a size is read as columns by rows", () => {
  assert.deepEqual(parseSize("4x2"), { columns: 4, rows: 2 });
  assert.deepEqual(parseSize("2x1"), { columns: 2, rows: 1 });
});

test("text that is not a size is refused", () => {
  for (const notASize of ["", "4", "x2", "0x1", "4x0", "4X2", "4 x 2", "-1x2", "2x1x1"]) {
    assert.throws(() => parseSize(notASize), /Not a widget size/, notASize);
  }
});

test("the area of a widget is its top left cell and its size", () => {
  assert.deepEqual(areaOf(widget("4x2", 1, 2)), { col: 1, row: 2, columns: 4, rows: 2 });
});

test("a widget fits when all of it is inside the grid", () => {
  assert.ok(fitsInsideGrid(GRID, areaOf(widget("4x2", 0, 0))));
  assert.ok(fitsInsideGrid(GRID, areaOf(widget("4x2", 2, 2))));   // touching the far corner
  assert.ok(!fitsInsideGrid(GRID, areaOf(widget("4x2", 3, 0))));  // one column too far right
  assert.ok(!fitsInsideGrid(GRID, areaOf(widget("4x2", 0, 3))));  // one row too far down
  assert.ok(!fitsInsideGrid(GRID, areaOf(widget("2x1", -1, 0))));
  assert.ok(!fitsInsideGrid(GRID, areaOf(widget("2x1", 0, -1))));
});

test("widgets that share a cell overlap, and widgets that only touch do not", () => {
  const big = areaOf(widget("4x2", 0, 0));
  assert.ok(areasOverlap(big, areaOf(widget("2x1", 3, 1))));    // shares the corner cell
  assert.ok(areasOverlap(big, areaOf(widget("2x1", 1, 0))));    // fully inside
  assert.ok(!areasOverlap(big, areaOf(widget("2x1", 4, 0))));   // side by side
  assert.ok(!areasOverlap(big, areaOf(widget("2x1", 0, 2))));   // directly below
});

test("overlap does not depend on which widget is asked first", () => {
  const first = areaOf(widget("2x2", 1, 1));
  const second = areaOf(widget("2x1", 2, 2));
  assert.equal(areasOverlap(first, second), areasOverlap(second, first));
});

test("a widget may be placed on free cells only", () => {
  const widgets = [widget("4x2", 0, 0), widget("2x1", 4, 3)];
  assert.ok(canPlace(GRID, widgets, { size: "2x1", col: 4, row: 0 }));
  assert.ok(!canPlace(GRID, widgets, { size: "2x1", col: 3, row: 1 }));   // overlaps the big one
  assert.ok(!canPlace(GRID, widgets, { size: "2x1", col: 5, row: 0 }));   // leaves the grid
});

test("a widget being moved does not block itself", () => {
  const widgets = [widget("4x2", 0, 0), widget("2x1", 4, 3)];
  assert.ok(!canPlace(GRID, widgets, { size: "4x2", col: 1, row: 0 }));
  assert.ok(canPlace(GRID, widgets, { size: "4x2", col: 1, row: 0 }, 0));
  assert.ok(!canPlace(GRID, widgets, { size: "4x2", col: 2, row: 2 }, 0));   // still blocked by the other
});

test("the first free place is found reading the grid like a page", () => {
  assert.deepEqual(firstFreePlace(GRID, [], "2x1"), { col: 0, row: 0 });
  assert.deepEqual(firstFreePlace(GRID, [widget("4x2", 0, 0)], "2x1"), { col: 4, row: 0 });
  assert.deepEqual(firstFreePlace(GRID, [widget("4x2", 0, 0)], "4x2"), { col: 0, row: 2 });
});

test("there is no free place on a full screen", () => {
  const full = [widget("4x2", 0, 0), widget("4x2", 0, 2), widget("2x2", 4, 0), widget("2x2", 4, 2)];
  assert.equal(firstFreePlace(GRID, full, "2x1"), null);
});

test("there may be room for a small widget and none for a large one", () => {
  const widgets = [widget("4x2", 0, 0), widget("4x2", 2, 2)];
  assert.notEqual(firstFreePlace(GRID, widgets, "2x1"), null);
  assert.equal(firstFreePlace(GRID, widgets, "4x2"), null);
});

test("a dragged widget snaps to the nearest cell", () => {
  assert.deepEqual(snapToGrid(GRID, "2x1", 2.4, 1.4), { col: 2, row: 1 });
  assert.deepEqual(snapToGrid(GRID, "2x1", 2.6, 1.6), { col: 3, row: 2 });
});

test("a dragged widget never snaps outside the grid", () => {
  assert.deepEqual(snapToGrid(GRID, "4x2", -3, -3), { col: 0, row: 0 });
  assert.deepEqual(snapToGrid(GRID, "4x2", 9, 9), { col: 2, row: 2 });
  assert.deepEqual(snapToGrid(GRID, "2x1", 5.4, 3.4), { col: 4, row: 3 });
});
