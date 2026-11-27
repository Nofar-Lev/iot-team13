// Shared by the desktop editor and the phone editor: a dialog that covers the editor and shows
// one message (session_messages.js describes them). The elements are the same in both
// editors; each editor's style sheet gives them its own look.
//
// One dialog shows at a time: showing a new message replaces the one on the screen. While a
// dialog is up, nothing behind it can be clicked, typed into or reached with the keyboard.

import { el } from "../common/dom.js";
import { icon } from "../common/icons.js";
import { countdownStage } from "./session_messages.js";

// How often a countdown is redrawn. The bar moves smoothly between redraws (a style rule).
const REDRAW_COUNTDOWN_EVERY_MS = 250;

/**
 * holder:         the element the dialog covers.
 * elementsBehind: the parts of the page that must not be usable while a dialog is up.
 * Returns { show(message), close(), isShowing(), showing() }.
 */
export function createDialog({ holder, elementsBehind = [] }) {
  const backdrop = el("div", "dialog-backdrop");
  backdrop.id = "dialog";
  backdrop.hidden = true;
  holder.append(backdrop);

  let dismiss = null;          // what a click beside the dialog, or Escape, does; or null
  let countdownTimer = null;

  function stopCountdown() {
    clearInterval(countdownTimer);
    countdownTimer = null;
  }

  function close() {
    stopCountdown();
    dismiss = null;
    backdrop.hidden = true;
    backdrop.replaceChildren();
    delete backdrop.dataset.message;
    for (const element of elementsBehind) element.inert = false;
  }

  function buildButton({ name, label, explanation, look, onClick }) {
    const button = el("button", `dialog__button dialog__button--${look}`);
    button.type = "button";
    button.dataset.action = name;
    button.append(el("span", "dialog__button-label", label));
    if (explanation) {
      button.classList.add("dialog__button--explained");
      button.append(el("span", "dialog__button-explanation", explanation));
    }
    // A button answers once: a second click while the answer is on its way does nothing.
    button.addEventListener("click", () => {
      for (const other of backdrop.querySelectorAll("button")) other.disabled = true;
      dismiss = null;
      onClick();
    });
    return button;
  }

  function buildCountdown({ seconds, warnsAsItRunsOut, label }) {
    const bar = el("div", "dialog__countdown-bar");
    const filling = el("div", "dialog__countdown-filling");
    bar.append(filling);
    const text = el("p", "dialog__countdown-text");
    const countdown = el("div", "dialog__countdown");
    countdown.append(bar, text);

    const startedAt = performance.now();
    function redraw() {
      const secondsLeft = Math.max(0, seconds - (performance.now() - startedAt) / 1000);
      const partLeft = seconds > 0 ? secondsLeft / seconds : 0;
      filling.style.width = `${partLeft * 100}%`;
      text.textContent = label(Math.ceil(secondsLeft));
      countdown.dataset.stage = warnsAsItRunsOut ? countdownStage(partLeft) : "calm";
      // At zero the dialog stays as it is: the server says what happened, and that news
      // replaces this message.
      if (secondsLeft === 0) stopCountdown();
    }
    redraw();
    countdownTimer = setInterval(redraw, REDRAW_COUNTDOWN_EVERY_MS);
    return countdown;
  }

  function show(message) {
    close();

    const title = el("h2", "dialog__title", message.title);
    title.id = "dialog-title";
    const dialog = el("div", "dialog");
    dialog.setAttribute("role", "dialog");
    dialog.setAttribute("aria-modal", "true");
    dialog.setAttribute("aria-labelledby", title.id);
    // The dialog itself takes the keyboard, not one of its buttons: a message can appear
    // while the user is typing, and a key meant for a text box must not press "Approve".
    dialog.tabIndex = -1;
    dialog.append(title);

    if (message.text) dialog.append(el("p", "dialog__text", message.text));
    if (message.countdown) dialog.append(buildCountdown(message.countdown));

    const buttons = el("div", "dialog__buttons");
    if (message.stacked) buttons.classList.add("dialog__buttons--stacked");
    buttons.append(...message.buttons.map(buildButton));
    dialog.append(buttons);

    if (message.dismiss) {
      const { label, onClick } = message.dismiss;
      dismiss = () => {
        close();
        onClick();
      };

      const quietLine = el("button", "dialog__dismiss-line", label);
      quietLine.type = "button";
      quietLine.dataset.action = "dismiss";
      quietLine.addEventListener("click", dismiss);

      const closeButton = el("button", "dialog__close");
      closeButton.type = "button";
      closeButton.dataset.action = "dismiss-with-x";
      closeButton.setAttribute("aria-label", label);
      closeButton.append(icon("close"));
      closeButton.addEventListener("click", dismiss);

      dialog.append(quietLine, closeButton);
    }

    backdrop.dataset.message = message.name;
    backdrop.append(dialog);
    for (const element of elementsBehind) element.inert = true;
    backdrop.hidden = false;
    dialog.focus();
  }

  // Beside the dialog, and the Escape key: the quiet way out, where the message has one.
  backdrop.addEventListener("click", (event) => {
    if (event.target === backdrop && dismiss) dismiss();
  });
  window.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && dismiss) dismiss();
  });

  return {
    show,
    close,
    isShowing: () => !backdrop.hidden,
    /** The name of the message on the screen, or null. */
    showing: () => backdrop.dataset.message ?? null,
  };
}
