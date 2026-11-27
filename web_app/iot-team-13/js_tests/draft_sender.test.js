// Tests for the sender that keeps the server's draft up to date.
// Run with:  node --test   (from the web_app folder)
//
// The server is replaced by a stand-in whose answers wait until the test lets them through,
// so the tests can make changes while a layout is still on its way.

import assert from "node:assert/strict";
import { test } from "node:test";

import { createDraftSender } from "../static/js/editing/draft_sender.js";

const layoutWith = (marker) => ({ version: 1, screens: [{ background: marker, widgets: [] }] });
const aMoment = () => new Promise((resolve) => setTimeout(resolve, 0));

/** A stand-in server, and a sender that sends to it. */
function newSender() {
  const server = { received: [], waiting: [], failures: [] };
  const sender = createDraftSender({
    send: (layout) => new Promise((resolve, reject) => {
      server.received.push(layout.screens[0].background);
      server.waiting.push({ resolve, reject });
    }),
    onCouldNotSend: (error) => server.failures.push(error.message),
  });
  /** Let the oldest travelling layout arrive, with this outcome. */
  server.answer = async (outcome = { accepted: true }) => {
    server.waiting.shift().resolve(outcome);
    await aMoment();
  };
  server.fail = async (message = "unreachable") => {
    server.waiting.shift().reject(new Error(message));
    await aMoment();
  };
  sender.startFrom(layoutWith("saved"));
  return { sender, server };
}

test("a changed layout is sent", () => {
  const { sender, server } = newSender();
  sender.layoutChanged(layoutWith("first change"));
  assert.deepEqual(server.received, ["first change"]);
});

test("a layout that is what the server already has is not sent", () => {
  const { sender, server } = newSender();
  sender.layoutChanged(layoutWith("saved"));
  assert.deepEqual(server.received, []);
});

test("the same change told twice is sent once", async () => {
  const { sender, server } = newSender();
  sender.layoutChanged(layoutWith("first change"));
  sender.layoutChanged(layoutWith("first change"));
  await server.answer();
  assert.deepEqual(server.received, ["first change"]);
});

test("one layout travels at a time, and of those that waited only the newest is sent", async () => {
  const { sender, server } = newSender();
  sender.layoutChanged(layoutWith("a"));
  sender.layoutChanged(layoutWith("ab"));
  sender.layoutChanged(layoutWith("abc"));
  assert.deepEqual(server.received, ["a"]);

  await server.answer();
  assert.deepEqual(server.received, ["a", "abc"]);

  await server.answer();
  assert.deepEqual(server.received, ["a", "abc"]);
});

test("a change back to what was saved is sent, so the server can drop the draft", async () => {
  const { sender, server } = newSender();
  sender.layoutChanged(layoutWith("changed"));
  await server.answer();
  sender.layoutChanged(layoutWith("saved"));
  assert.deepEqual(server.received, ["changed", "saved"]);
});

test("the sender keeps its own copy, so later edits do not change what is on its way", async () => {
  const { sender, server } = newSender();
  const layout = layoutWith("a");
  sender.layoutChanged(layout);
  layout.screens[0].background = "ab";   // the editor goes on changing the same object
  sender.layoutChanged(layout);
  await server.answer();
  assert.deepEqual(server.received, ["a", "ab"]);
});

test("waiting for everything to be sent waits for the layout on its way and the one behind it", async () => {
  const { sender, server } = newSender();
  sender.layoutChanged(layoutWith("a"));
  sender.layoutChanged(layoutWith("ab"));
  let isEverythingSent = false;
  sender.whenEverythingIsSent().then(() => { isEverythingSent = true; });

  await server.answer();
  assert.equal(isEverythingSent, false);
  await server.answer();
  assert.equal(isEverythingSent, true);
});

test("with nothing on its way, everything is sent already", async () => {
  const { sender } = newSender();
  await sender.whenEverythingIsSent();
});

test("what the server finds wrong with a layout is remembered until a good one arrives", async () => {
  const { sender, server } = newSender();
  sender.layoutChanged(layoutWith("faulty"));
  await server.answer({ accepted: false, problems: ["A widget is outside the grid."] });
  assert.deepEqual(sender.problems(), ["A widget is outside the grid."]);
  assert.deepEqual(server.failures, []);   // a faulty layout is not a lost connection

  sender.layoutChanged(layoutWith("good again"));
  await server.answer();
  assert.equal(sender.problems(), null);
});

test("a layout that could not be delivered stops the sender, and the caller is told once", async () => {
  const { sender, server } = newSender();
  sender.layoutChanged(layoutWith("a"));
  sender.layoutChanged(layoutWith("ab"));
  await server.fail("unreachable");

  assert.deepEqual(server.failures, ["unreachable"]);
  assert.deepEqual(server.received, ["a"]);   // the one that waited is not sent
  sender.layoutChanged(layoutWith("abc"));
  assert.deepEqual(server.received, ["a"]);
  await sender.whenEverythingIsSent();        // and nobody waits for it forever
});

test("a stopped sender sends nothing more and tells nobody", async () => {
  const { sender, server } = newSender();
  sender.layoutChanged(layoutWith("a"));
  sender.layoutChanged(layoutWith("ab"));
  sender.stop();
  await server.fail("refused: no longer the editor in use");
  sender.layoutChanged(layoutWith("abc"));

  assert.deepEqual(server.received, ["a"]);
  assert.deepEqual(server.failures, []);
  await sender.whenEverythingIsSent();
});

test("starting from a new layout forgets a change that had not been sent yet", async () => {
  const { sender, server } = newSender();
  sender.layoutChanged(layoutWith("a"));
  sender.layoutChanged(layoutWith("ab"));
  sender.startFrom(layoutWith("saved"));   // for example after Discard
  await server.answer();
  assert.deepEqual(server.received, ["a"]);
});
