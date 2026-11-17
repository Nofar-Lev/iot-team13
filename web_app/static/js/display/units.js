// Small conversions used by the widgets.

/** A temperature as text, in the user's units: 23 -> "23°" or "73°". */
export function temperatureText(celsius, units, decimals = 0) {
  const value = units === "fahrenheit" ? (celsius * 9) / 5 + 32 : celsius;
  return `${value.toFixed(decimals)}°`;
}

/**
 * How many units of the "to" currency one unit of the "from" currency buys.
 * valueInUsd says what one unit of each currency is worth in US dollars.
 */
export function exchangeRate(valueInUsd, from, to) {
  return valueInUsd[from] / valueInUsd[to];
}
