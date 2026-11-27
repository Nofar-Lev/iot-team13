// Sends the layout being edited to the server's draft, change after change.
//
// One layout travels at a time. While it is on its way, newer changes wait, and only the
// newest of them is sent next: the draft is the whole layout, so the ones in between are not
// needed. A fast typist therefore never builds up a line of requests, and the server always
// receives the changes in the order they were made.
//
// No page elements and no network here: the caller hands over the function that does the
// actual sending.

const sameLayout = (one, other) => JSON.stringify(one) === JSON.stringify(other);
const copyOf = (value) => JSON.parse(JSON.stringify(value));

/**
 * send(layout): sends one layout. Resolves to { accepted: true }, or to
 *               { accepted: false, problems } when the server finds the layout faulty.
 *               Rejects when the layout could not be delivered at all.
 * onCouldNotSend(error): called once if send() rejects. Nothing is sent after that.
 */
export function createDraftSender({ send, onCouldNotSend }) {
  let layoutTheServerHas = null;   // as far as this page knows: the last one sent or on its way
  let waitingLayout = null;        // the newest change that has not been sent yet
  let sending = null;              // a promise while layouts are travelling, otherwise null
  let problems = null;             // what the server found wrong with the last layout it got
  let hasStopped = false;

  async function sendUntilNothingWaits() {
    try {
      while (waitingLayout !== null && !hasStopped) {
        const layout = waitingLayout;
        waitingLayout = null;
        const outcome = await send(layout);
        problems = outcome.accepted ? null : outcome.problems;
      }
    } catch (error) {
      if (!hasStopped) {
        hasStopped = true;
        onCouldNotSend(error);
      }
    }
  }

  function startSending() {
    sending = sendUntilNothingWaits().finally(() => {
      sending = null;
      // A change that arrived in the instant between the last send and this line still goes out.
      if (waitingLayout !== null && !hasStopped) startSending();
    });
  }

  return {
    /** The layout that the server holds at this moment, so that it is not sent again. */
    startFrom(layout) {
      layoutTheServerHas = copyOf(layout);
      waitingLayout = null;
      problems = null;
    },

    /** The layout as it is now. It is sent only if it differs from what the server has. */
    layoutChanged(layout) {
      if (hasStopped || sameLayout(layout, layoutTheServerHas)) return;
      layoutTheServerHas = copyOf(layout);
      waitingLayout = layoutTheServerHas;
      if (!sending) startSending();
    },

    /** Resolves when every change made so far has been sent, or sending has stopped. */
    async whenEverythingIsSent() {
      while (sending) await sending;
    },

    /** What the server found wrong with the last layout it received, or null. */
    problems: () => problems,

    /** Send nothing more, for example because this editor is no longer the one in use. */
    stop() {
      hasStopped = true;
      waitingLayout = null;
    },
  };
}
