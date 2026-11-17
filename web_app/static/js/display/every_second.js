// One shared ticker: calls every listener once a second, right as the second changes, so all
// the clocks on a page change together.

const listeners = new Set();
let timer = null;

function tick() {
  const now = new Date();
  for (const listener of listeners) listener(now);
  scheduleNextTick();
}

function scheduleNextTick() {
  const untilNextSecond = 1000 - (Date.now() % 1000);
  timer = setTimeout(tick, untilNextSecond + 5);
}

/** Call listener(now) every second. Returns a function that stops it. */
export function everySecond(listener) {
  listeners.add(listener);
  if (timer === null) scheduleNextTick();
  return () => {
    listeners.delete(listener);
    if (listeners.size === 0) {
      clearTimeout(timer);
      timer = null;
    }
  };
}
