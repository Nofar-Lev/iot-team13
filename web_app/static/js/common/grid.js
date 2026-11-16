// Grid arithmetic: where a widget may sit. No page elements here, so it is easy to test.
//
// A grid is { columns, rows }. A widget's place is its top left cell (col, row) and its size,
// written like "4x2": 4 columns wide and 2 rows tall.

/** "4x2" -> { columns: 4, rows: 2 } */
export function parseSize(size) {
  const match = /^([1-9]\d*)x([1-9]\d*)$/.exec(size);
  if (!match) throw new Error(`Not a widget size: "${size}"`);
  return { columns: Number(match[1]), rows: Number(match[2]) };
}

/** The cells a widget covers, as a rectangle. */
export function areaOf(widget) {
  const { columns, rows } = parseSize(widget.size);
  return { col: widget.col, row: widget.row, columns, rows };
}

export function fitsInsideGrid(grid, area) {
  return (
    area.col >= 0 &&
    area.row >= 0 &&
    area.col + area.columns <= grid.columns &&
    area.row + area.rows <= grid.rows
  );
}

export function areasOverlap(first, second) {
  return (
    first.col < second.col + second.columns &&
    second.col < first.col + first.columns &&
    first.row < second.row + second.rows &&
    second.row < first.row + first.rows
  );
}

/**
 * May a widget of this size sit at (col, row)?
 * ignoreIndex names a widget to leave out of the check: the one being moved.
 */
export function canPlace(grid, widgets, candidate, ignoreIndex = -1) {
  const candidateArea = areaOf(candidate);
  if (!fitsInsideGrid(grid, candidateArea)) return false;
  return !widgets.some(
    (widget, index) => index !== ignoreIndex && areasOverlap(areaOf(widget), candidateArea),
  );
}

/** The first free place for a widget of this size, reading the grid like a page. Null if none. */
export function firstFreePlace(grid, widgets, size) {
  for (let row = 0; row < grid.rows; row += 1) {
    for (let col = 0; col < grid.columns; col += 1) {
      if (canPlace(grid, widgets, { size, col, row })) return { col, row };
    }
  }
  return null;
}

/**
 * The cell a dragged widget snaps to.
 * left and top say where the widget's top left corner is, measured in cells and not yet
 * rounded (2.4 means "two cells and a bit"). The answer is always inside the grid.
 */
export function snapToGrid(grid, size, left, top) {
  const { columns, rows } = parseSize(size);
  const keepInside = (value, largest) => Math.min(Math.max(value, 0), Math.max(largest, 0));
  return {
    col: keepInside(Math.round(left), grid.columns - columns),
    row: keepInside(Math.round(top), grid.rows - rows),
  };
}
