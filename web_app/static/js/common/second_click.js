// For buttons that throw work away: the first click asks, the second click (soon after) does it.
// Gentler than a pop-up window, and there is nothing to dismiss.

const SECOND_CLICK_WITHIN_MS = 3000;

/**
 * button, labelElement: the button and the element inside it that holds its text.
 * usualText, askingText: the label normally, and after the first click.
 * shouldAsk():           return false to skip the question (nothing would be lost).
 * onConfirmed():         called when the action should really happen.
 * Returns { reset() } to put the button back to normal from outside.
 */
export function askForSecondClick({ button, labelElement, usualText, askingText, shouldAsk, onConfirmed }) {
  let timer = null;

  function reset() {
    clearTimeout(timer);
    timer = null;
    labelElement.textContent = usualText;
    button.classList.remove("button--danger");
  }

  button.addEventListener("click", () => {
    if (timer === null && shouldAsk()) {
      labelElement.textContent = askingText;
      button.classList.add("button--danger");
      timer = setTimeout(reset, SECOND_CLICK_WITHIN_MS);
      return;
    }
    reset();
    onConfirmed();
  });

  reset();
  return { reset };
}
