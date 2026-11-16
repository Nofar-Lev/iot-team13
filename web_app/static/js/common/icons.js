// The small pictures used on the display and in the pages, drawn as vector shapes.
// All of them were drawn for this project, so there is no licence to keep track of.

const LINE = 'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"';

const CLOUD = "M14 38a8 8 0 0 1-1.2-15.9 11 11 0 0 1 21.4 2.2A7 7 0 0 1 34 38H14z";

const ICONS = {
  // --- Weather, in two colours, on a 48x48 drawing ---
  weather_sunny: { box: 48, shapes: '<circle cx="24" cy="24" r="10" fill="#ffd27a"/>' },
  weather_partly_cloudy: {
    box: 48,
    shapes: `<circle cx="32" cy="17" r="8.5" fill="#ffd27a"/><path d="${CLOUD}" fill="#ffffff"/>`,
  },
  weather_cloudy: { box: 48, shapes: `<path d="${CLOUD}" fill="#ffffff"/>` },
  weather_rainy: {
    box: 48,
    shapes: `<path d="${CLOUD}" fill="#ffffff" transform="translate(0 -6)"/>
             <path d="M17 37l-2 6M25 37l-2 6M33 37l-2 6" fill="none" stroke="#a8d4ff" stroke-width="2.5" stroke-linecap="round"/>`,
  },

  // --- Connection ---
  connected: {
    box: 24,
    shapes: `<path d="M3.51 10.51a12 12 0 0 1 16.98 0M6.34 13.34a8 8 0 0 1 11.32 0M9.17 16.17a4 4 0 0 1 5.66 0" ${LINE}/>
             <circle cx="12" cy="19.5" r="1.4" fill="currentColor"/>`,
  },
  not_connected: {
    box: 24,
    shapes: `<path d="M3.51 10.51a12 12 0 0 1 16.98 0M6.34 13.34a8 8 0 0 1 11.32 0M9.17 16.17a4 4 0 0 1 5.66 0" ${LINE} opacity="0.45"/>
             <circle cx="12" cy="19.5" r="1.4" fill="currentColor" opacity="0.45"/>
             <path d="M4.5 4.5l15 16" ${LINE}/>`,
  },

  // --- Small marks used inside widgets and lists ---
  thermometer: { box: 24, shapes: `<path d="M12 4a2 2 0 0 0-2 2v8.3a4 4 0 1 0 4 0V6a2 2 0 0 0-2-2z" ${LINE}/>` },
  droplet: { box: 24, shapes: `<path d="M12 3.5c3 3.8 5.5 6.6 5.5 10a5.5 5.5 0 0 1-11 0c0-3.4 2.5-6.2 5.5-10z" ${LINE}/>` },
  arrow_right: { box: 24, shapes: `<path d="M5 12h14M13 6l6 6-6 6" ${LINE}/>` },
  going_up: { box: 24, shapes: '<path d="M12 6l8 12H4z" fill="currentColor"/>' },
  going_down: { box: 24, shapes: '<path d="M12 18L4 6h16z" fill="currentColor"/>' },
  reminder_done: {
    box: 24,
    shapes: `<circle cx="12" cy="12" r="10" fill="currentColor"/>
             <path d="M7.5 12.5l3 3 6-6.5" fill="none" stroke="var(--tick-colour, #1d2b3a)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>`,
  },
  reminder_missed: {
    box: 24,
    shapes: `<circle cx="12" cy="12" r="9" ${LINE}/><path d="M12 7.5v5.5" ${LINE}/><circle cx="12" cy="16.5" r="1.2" fill="currentColor"/>`,
  },
  reminder_waiting: { box: 24, shapes: `<circle cx="12" cy="12" r="9" ${LINE}/>` },

  // --- Buttons in the pages ---
  back: { box: 24, shapes: `<path d="M15 5l-7 7 7 7" ${LINE}/>` },
  forward: { box: 24, shapes: `<path d="M9 5l7 7-7 7" ${LINE}/>` },
  plus: { box: 24, shapes: `<path d="M12 5v14M5 12h14" ${LINE}/>` },
  close: { box: 24, shapes: `<path d="M6 6l12 12M18 6L6 18" ${LINE}/>` },
  pencil: { box: 24, shapes: `<path d="M4 20l1-4L16.5 4.5a2.1 2.1 0 0 1 3 3L8 19l-4 1z" ${LINE}/>` },
  trash: { box: 24, shapes: `<path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13" ${LINE}/>` },
  microphone: {
    box: 24,
    shapes: `<rect x="9" y="3" width="6" height="11" rx="3" ${LINE}/><path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21" ${LINE}/>`,
  },
  full_screen: { box: 24, shapes: `<path d="M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5" ${LINE}/>` },
};

/** A new picture element. Its size and colour come from the page's styles. */
export function icon(name, className = "") {
  const drawing = ICONS[name];
  if (!drawing) throw new Error(`There is no icon named "${name}"`);
  const holder = document.createElement("span");
  holder.className = `icon ${className}`.trim();
  holder.setAttribute("aria-hidden", "true");
  // Safe: the shapes come from the table above, never from anything a user typed.
  holder.innerHTML = `<svg viewBox="0 0 ${drawing.box} ${drawing.box}" xmlns="http://www.w3.org/2000/svg">${drawing.shapes}</svg>`;
  return holder;
}

export function hasIcon(name) {
  return name in ICONS;
}
