// A tap on the space around the preview lets go of the selected widget.
//
// Taps on the preview itself are read by preview_touches.js, and the round arrows have their
// own work. The panel is not part of the stage: a tap there never changes what is selected.

/**
 * stage:        the element that holds the preview and the space around it.
 * previewFrame: the preview's picture.
 * onTapBeside(): called for a tap on the stage that is not on the preview or on an arrow.
 */
export function setUpTapsBesideThePreview({ stage, previewFrame, onTapBeside }) {
  stage.addEventListener("click", (event) => {
    if (previewFrame.contains(event.target)) return;
    if (event.target.closest(".preview__arrow")) return;
    onTapBeside();
  });
}
