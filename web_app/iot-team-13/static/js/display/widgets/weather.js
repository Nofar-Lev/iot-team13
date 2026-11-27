// The weather. Sizes: 2x1 (icon, temperature, city) and 2x2 (adds the description and the
// day's high and low). Settings: city, Celsius or Fahrenheit.
// The numbers are example values for now; the city and the units are the user's.

import { el } from "../../common/dom.js";
import { hasIcon, icon } from "../../common/icons.js";
import { temperatureText } from "../units.js";

function weatherIcon(condition) {
  const name = `weather_${condition}`;
  return icon(hasIcon(name) ? name : "weather_cloudy", "weather__icon");
}

export function buildWeather(body, { size, settings, demoData }) {
  const weather = demoData.weather;
  const temperature = temperatureText(weather.temperature_celsius, settings.units);
  const city = settings.city.trim() || "—";

  const card = el("div", `weather weather--${size}`);

  if (size === "2x2") {
    const now = el("div", "weather__now");
    now.append(weatherIcon(weather.condition), el("span", "weather__temperature", temperature));
    const high = temperatureText(weather.high_celsius, settings.units);
    const low = temperatureText(weather.low_celsius, settings.units);
    card.append(
      el("div", "weather__city", city),
      now,
      el("div", "weather__description", weather.condition_label),
      el("div", "weather__range", `High ${high}  ·  Low ${low}`),
    );
  } else {
    const text = el("div", "weather__text");
    text.append(el("span", "weather__temperature", temperature), el("span", "weather__city", city));
    card.append(weatherIcon(weather.condition), text);
  }

  body.append(card);
}
