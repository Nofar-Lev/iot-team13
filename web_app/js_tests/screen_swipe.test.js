// Tests for what counts as a swipe between screens. Run with:  node --test js_tests/

import assert from "node:assert/strict";
import { test } from "node:test";

import { SHORTEST_SWIPE, screenStepOfSwipe } from "../static/js/editor_phone/screen_swipe.js";

const from = { x: 300, y: 200 };

test("a swipe to the left asks for the next screen", () => {
  assert.equal(screenStepOfSwipe(from, { x: 300 - 120, y: 200 }), +1);
});

test("a swipe to the right asks for the previous screen", () => {
  assert.equal(screenStepOfSwipe(from, { x: 300 + 120, y: 200 }), -1);
});

test("a tap, or a finger that barely moved, is not a swipe", () => {
  assert.equal(screenStepOfSwipe(from, from), 0);
  assert.equal(screenStepOfSwipe(from, { x: 300 - (SHORTEST_SWIPE - 1), y: 200 }), 0);
});

test("the shortest swipe that counts is exactly the limit", () => {
  assert.equal(screenStepOfSwipe(from, { x: 300 - SHORTEST_SWIPE, y: 200 }), +1);
  assert.equal(screenStepOfSwipe(from, { x: 300 + SHORTEST_SWIPE, y: 200 }), -1);
});

test("a movement that is more up-and-down than sideways is not a swipe", () => {
  assert.equal(screenStepOfSwipe(from, { x: 300 - 60, y: 200 + 90 }), 0);
  assert.equal(screenStepOfSwipe(from, { x: 300 + 60, y: 200 - 61 }), 0);
});

test("a slanted movement that is mostly sideways is a swipe", () => {
  assert.equal(screenStepOfSwipe(from, { x: 300 - 100, y: 200 + 40 }), +1);
});
