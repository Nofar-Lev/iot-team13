// The live channel: the page keeps one connection to the server open, and the server pushes
// news down it (a new layout was saved, the display went online or offline).
//
// The page also learns from it whether the server is reachable. The server sends a "heartbeat"
// every two seconds; if nothing at all arrives for a while, the connection is treated as lost.
//
// Most pages then open it again, until the server is back. An editor does not: to the server,
// an editor is its connection, so a lost connection is the end of that editor
// (editing/editing_session.js). It opens the channel with tryAgainWhenLost: false.

// The last five are sent to one editor only, about another editor taking over.
const NEWS_NAMES = [
  "hello", "layout", "display", "heartbeat",
  "take_over_request", "take_over_withdrawn", "taken_over", "take_over_refused", "take_over_granted",
];

// Three missed heartbeats.
const SILENCE_THAT_MEANS_LOST_MS = 6500;
const TRY_AGAIN_AFTER_MS = 1000;

/**
 * role:                "device", "home" or "editor": what this page is.
 * onNews(name, details): called for every piece of news except heartbeats.
 * onConnectionChange(isConnected): called when the connection is made or lost.
 * tryAgainWhenLost:    false opens the channel once. When it is lost, or cannot be opened at
 *                      all, onConnectionChange(false) is called and nothing more happens.
 */
export function openLiveChannel({ role, onNews, onConnectionChange = () => {}, tryAgainWhenLost = true }) {
  let source = null;
  let isConnected = false;
  let silenceTimer = null;
  let tryAgainTimer = null;
  let isClosedForGood = false;

  function setConnected(nowConnected) {
    if (nowConnected === isConnected) return;
    isConnected = nowConnected;
    onConnectionChange(isConnected);
  }

  function expectToHearSoon() {
    clearTimeout(silenceTimer);
    silenceTimer = setTimeout(connectionLost, SILENCE_THAT_MEANS_LOST_MS);
  }

  function heardFromServer() {
    setConnected(true);
    expectToHearSoon();
  }

  function connectionLost() {
    clearTimeout(silenceTimer);
    clearTimeout(tryAgainTimer);
    if (source) source.close();
    source = null;

    if (isClosedForGood || tryAgainWhenLost) {
      setConnected(false);
      if (!isClosedForGood) tryAgainTimer = setTimeout(connect, TRY_AGAIN_AFTER_MS);
      return;
    }
    // Opened once, and now lost: say so even if the connection was never made.
    isClosedForGood = true;
    isConnected = false;
    onConnectionChange(false);
  }

  function connect() {
    if (isClosedForGood) return;
    source = new EventSource(`/api/events?role=${encodeURIComponent(role)}`);
    source.onerror = connectionLost;
    for (const name of NEWS_NAMES) {
      source.addEventListener(name, (event) => {
        heardFromServer();
        if (name !== "heartbeat") onNews(name, JSON.parse(event.data));
      });
    }
    // A channel that is opened once must not wait forever for a server that never answers.
    if (!tryAgainWhenLost) expectToHearSoon();
  }

  // The channel is opened only once the page has finished loading. A connection that never
  // ends, opened while the page is still loading, makes some browsers show the page as
  // "loading" for as long as it stays open.
  if (document.readyState === "complete") connect();
  else window.addEventListener("load", connect, { once: true });

  return {
    close() {
      isClosedForGood = true;
      connectionLost();
    },
  };
}
