// TEMPORARY: shows the phone editor's mock-up pictures at their real size on a phone.
//
// The pictures were made at a few common phone sizes, with the phone held sideways and the
// page in full screen. This page goes full screen, measures the phone's screen, picks the set
// of pictures made for the closest size, and shows one picture at a time. A tap anywhere moves
// to the next picture; after the last one it starts again.

// The sizes the pictures were made at, in page units (width x height, phone held sideways).
// Each set is a folder next to this file.
const PICTURE_SETS = [
  { width: 780, height: 360 },
  { width: 832, height: 384 },
  { width: 915, height: 412 },
];

// The pictures of one set, in the order they are shown.
const PICTURES = [
  { file: "01-main-menu.jpg", title: "The editing screen, with the main menu" },
  { file: "02-last-screen-add-arrow.jpg", title: "The last screen: the right arrow adds a screen" },
  { file: "03-add-a-widget.jpg", title: "Add a widget: tap to add, hold to carry" },
  { file: "04-clock-sizes.jpg", title: "The clock's sizes" },
  { file: "05-widget-options.jpg", title: "A widget's options, with Back" },
  { file: "06-backgrounds.jpg", title: "Backgrounds" },
  { file: "07-holding-a-widget.jpg", title: "A held widget: the panel shows its options" },
  { file: "08-remove-screen-asks.jpg", title: "Remove this screen, after the first tap" },
];

// How long the caption stays before it fades.
const CAPTION_STAYS_FOR_MS = 2200;

const start = document.getElementById("start");
const startNote = document.getElementById("start-note");
const viewer = document.getElementById("viewer");
const picture = document.getElementById("picture");
const caption = document.getElementById("caption");
const turnMessage = document.getElementById("turn-message");

let pictureIndex = 0;
let captionTimer = null;

/** The screen as the page sees it now, with the longer side as its width. */
function screenHeldSideways() {
  return {
    width: Math.max(window.innerWidth, window.innerHeight),
    height: Math.min(window.innerWidth, window.innerHeight),
  };
}

/**
 * The set of pictures made for the size closest to this screen. The height decides, because
 * the display in the editor is as tall as the screen; among equal heights, the width does.
 */
export function closestPictureSet(screen, sets = PICTURE_SETS) {
  const distance = (set) => Math.abs(set.height - screen.height) * 10 + Math.abs(set.width - screen.width);
  return sets.reduce((best, set) => (distance(set) < distance(best) ? set : best));
}

function showCaption(text) {
  caption.textContent = text;
  caption.classList.add("viewer__caption--showing");
  clearTimeout(captionTimer);
  captionTimer = setTimeout(() => caption.classList.remove("viewer__caption--showing"), CAPTION_STAYS_FOR_MS);
}

function showPicture() {
  const screen = screenHeldSideways();
  const set = closestPictureSet(screen);
  const shown = PICTURES[pictureIndex];

  picture.src = `/static/phone-mockups/${set.width}x${set.height}/${shown.file}`;
  picture.alt = shown.title;

  const isExactSize = set.width === screen.width && set.height === screen.height;
  const sizeNote = isExactSize
    ? `true size for this screen (${screen.width} x ${screen.height})`
    : `this screen is ${screen.width} x ${screen.height}, the picture was made for ${set.width} x ${set.height}`;
  showCaption(`${pictureIndex + 1} of ${PICTURES.length}: ${shown.title}  |  ${sizeNote}`);

  // The pictures are sideways. A phone held upright is asked to turn.
  turnMessage.hidden = window.innerWidth >= window.innerHeight;
}

/** Fetch the other pictures of the set now, so that a tap shows the next one at once. */
function preloadPictures() {
  const set = closestPictureSet(screenHeldSideways());
  for (const { file } of PICTURES) new Image().src = `/static/phone-mockups/${set.width}x${set.height}/${file}`;
}

/** Full screen, with the picture held sideways. Both are tried; neither is required. */
async function goFullScreenSideways() {
  const page = document.documentElement;
  let wentFullScreen = false;
  try {
    if (page.requestFullscreen) {
      await page.requestFullscreen();
      wentFullScreen = true;
    }
  } catch {
    // The browser said no. The pictures still show, a little smaller, under the browser's bars.
  }
  try {
    await screen.orientation?.lock?.("landscape");
  } catch {
    // Not every browser lets a page hold the picture sideways. The user turns the phone.
  }
  return wentFullScreen;
}

async function startViewing() {
  const wentFullScreen = await goFullScreenSideways();
  start.hidden = true;
  viewer.hidden = false;
  showPicture();
  preloadPictures();
  viewer.dataset.fullScreen = String(wentFullScreen);
}

function stopViewing() {
  viewer.hidden = true;
  start.hidden = false;
  startNote.textContent = "Full screen was left. Tap the button to go on.";
}

document.getElementById("start-button").addEventListener("click", startViewing);

viewer.addEventListener("click", () => {
  pictureIndex = (pictureIndex + 1) % PICTURES.length;
  showPicture();
});

// Turning the phone, or the browser's bars appearing, changes the screen's size.
window.addEventListener("resize", () => {
  if (!viewer.hidden) showPicture();
});

// Leaving full screen (the phone's Back gesture) returns to the start screen.
document.addEventListener("fullscreenchange", () => {
  if (document.fullscreenElement === null && viewer.dataset.fullScreen === "true") stopViewing();
});
