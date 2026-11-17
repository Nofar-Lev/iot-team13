// The room's temperature and humidity, from the device's own sensor. Size 2x1.
// Setting: Celsius or Fahrenheit. The readings are example values for now.

import { el } from "../../common/dom.js";
import { icon } from "../../common/icons.js";
import { temperatureText } from "../units.js";

function reading(iconName, text) {
  const holder = el("span", "room__reading");
  holder.append(icon(iconName), el("span", "", text));
  return holder;
}

export function buildRoomClimate(body, { settings, demoData }) {
  const room = demoData.room_climate;

  const readings = el("div", "room__readings");
  readings.append(
    reading("thermometer", temperatureText(room.temperature_celsius, settings.units, 1)),
    reading("droplet", `${room.humidity_percent}%`),
  );

  const card = el("div", "room");
  card.append(el("div", "room__title", "Room"), readings);
  body.append(card);
}
