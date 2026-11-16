// Tests for the helper that keeps a page's copy of the layout up to date.
// Run with:  node --test js_tests/
//
// The server is replaced by a stand-in: a function that answers "fetch" with whatever
// revision the test says the server has. Nothing here uses the network.

import assert from "node:assert/strict";
import { afterEach, test } from "node:test";

import { createLayoutFollower } from "../static/js/common/layout_follower.js";

const realFetch = globalThis.fetch;
afterEach(() => {
  globalThis.fetch = realFetch;
});

/** A stand-in server. Each fetch waits until the test lets it answer. */
function standInServer() {
  const server = { revision: 0, isReachable: true, fetchCount: 0, waiting: [] };
  globalThis.fetch = () => {
    server.fetchCount += 1;
    return new Promise((resolve, reject) => {
      server.waiting.push(() => {
        if (!server.isReachable) return reject(new TypeError("fetch failed"));
        const body = { revision: server.revision, saved_at: null, layout: { marker: server.revision } };
        resolve({ ok: true, status: 200, json: async () => body });
      });
    });
  };
  /** Let the oldest waiting fetch answer, and give the follower time to act on it. */
  server.answerOne = async () => {
    server.waiting.shift()();
    await new Promise((resolve) => setTimeout(resolve, 0));
  };
  return server;
}

test("the layout is fetched when the server mentions a revision the page does not have", async () => {
  const server = standInServer();
  const received = [];
  const catchUpWith = createLayoutFollower({ onLayout: (saved) => received.push(saved.revision) });

  catchUpWith(0);
  await server.answerOne();
  assert.deepEqual(received, [0]);
});

test("nothing is fetched when the page already has that revision", async () => {
  const server = standInServer();
  const catchUpWith = createLayoutFollower({ onLayout: () => {} });
  catchUpWith(0);
  await server.answerOne();

  await catchUpWith(0);
  assert.equal(server.fetchCount, 1);
});

test("news that arrives during a fetch does not start a second fetch when one is enough", async () => {
  const server = standInServer();
  const received = [];
  const catchUpWith = createLayoutFollower({ onLayout: (saved) => received.push(saved.revision) });

  server.revision = 1;
  catchUpWith(1);              // a fetch is on its way...
  server.revision = 2;
  catchUpWith(2);              // ...when news of another save arrives
  await server.answerOne();    // the answer already carries revision 2
  assert.deepEqual(received, [2]);
  assert.equal(server.fetchCount, 1);
});

test("a save that happens during a fetch is not lost: the page fetches again", async () => {
  const server = standInServer();
  const received = [];
  const catchUpWith = createLayoutFollower({ onLayout: (saved) => received.push(saved.revision) });

  server.revision = 1;
  catchUpWith(1);
  await server.answerOne();    // the page now has revision 1
  catchUpWith(2);              // news of revision 2, but the stand-in still answers with 1
  await server.answerOne();
  assert.equal(server.waiting.length, 1, "it must ask again, because it is still behind");
  server.revision = 2;
  await server.answerOne();
  assert.deepEqual(received, [1, 1, 2]);
  assert.equal(server.waiting.length, 0);
});

test("the page is not confused when the server is already past the number in the news", async () => {
  const server = standInServer();
  const received = [];
  const catchUpWith = createLayoutFollower({ onLayout: (saved) => received.push(saved.revision) });

  server.revision = 5;
  catchUpWith(4);
  await server.answerOne();
  assert.deepEqual(received, [5]);
  assert.equal(server.waiting.length, 0, "it must not keep fetching to find revision 4");
});

test("an unreachable server is survived, and the page catches up afterwards", async () => {
  const server = standInServer();
  const received = [];
  const catchUpWith = createLayoutFollower({ onLayout: (saved) => received.push(saved.revision) });

  server.isReachable = false;
  catchUpWith(3);
  await server.answerOne();
  assert.deepEqual(received, []);

  server.isReachable = true;
  server.revision = 3;
  catchUpWith(3);              // the "hello" after reconnecting
  await server.answerOne();
  assert.deepEqual(received, [3]);
});
