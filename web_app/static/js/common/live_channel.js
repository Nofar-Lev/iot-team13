// The live channel: the page keeps one connection to the server open, and the server pushes
// news down it (a new layout was saved, the display went online or offline).
//
// The page also learns from it whether the server is reachable. The server sends a "heartbeat"
// every two seconds; if nothing at all arrives for a while, the connection is treated as lost
// and opened again, until the server is back.

const NEWS_NAMES = ["hello", "layout", "display", "heartbeat"];

// Three missed heartbeats.
const SILENCE_THAT_MEANS_LOST_MS = 6500;
const TRY_AGAIN_AFTER_MS = 1000;

/**
 * role:                "device", "home" or "editor": what this page is.
 * onNews(name, details): called for every piece of news except heartbeats.
 * onConnectionChange(isConnected): called when the connection is made or lost.
 */
export function openLiveChannel({ role, onNews, onConnectionChange = () => {} }) {
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

  function heardFromServer() {
    setConnected(true);
    clearTimeout(silenceTimer);
    silenceTimer = setTimeout(connectionLost, SILENCE_THAT_MEANS_LOST_MS);
  }

  function connectionLost() {
    setConnected(false);
    clearTimeout(silenceTimer);
    clearTimeout(tryAgainTimer);
    if (source) source.close();
    source = null;
    if (!isClosedForGood) tryAgainTimer = setTimeout(connect, TRY_AGAIN_AFTER_MS);
  }

  function connect() {
    source = new EventSource(`/api/events?role=${encodeURIComponent(role)}`);
    source.onerror = connectionLost;
    for (const name of NEWS_NAMES) {
      source.addEventListener(name, (event) => {
        heardFromServer();
        if (name !== "heartbeat") onNews(name, JSON.parse(event.data));
      });
    }
  }

  connect();

  return {
    close() {
      isClosedForGood = true;
      connectionLost();
    },
  };
}
