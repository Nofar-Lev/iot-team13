// The settings of the selected widget. The form is built from the widget catalog, so a new
// setting in the catalog appears here without any change to this file.
//
// The kinds of setting: "choice" (one of a few values), "toggle" (on or off), "text", and
// "number". A number whose catalog entry says editor "time_picker" is shown as a time of day.

import { el } from "../common/dom.js";
import { icon } from "../common/icons.js";
import { chosenTimeForOffset, offsetForChosenTime } from "../display/time_formats.js";

// Choices are shown as a row of buttons when their labels are short, and as a drop-down list
// when they are long.
const LONGEST_LABELS_FOR_BUTTON_ROW = 26;

export function setUpSettingsPanel(panelElement, state) {
  // The rows of the form being shown, so their visibility can be updated.
  let shownRows = [];

  // --- One control per kind of setting --------------------------------------------------------

  function choiceControl(setting, widget) {
    const totalLabelLength = setting.choices.reduce((sum, choice) => sum + choice.label.length, 0);

    if (totalLabelLength > LONGEST_LABELS_FOR_BUTTON_ROW) {
      const list = el("select", "field__select");
      for (const choice of setting.choices) {
        const option = el("option", "", choice.label);
        option.value = choice.value;
        list.append(option);
      }
      list.value = widget.settings[setting.key];
      list.addEventListener("change", () => changeSetting(setting.key, list.value));
      return list;
    }

    const buttonRow = el("div", "choice-row");
    for (const choice of setting.choices) {
      const button = el("button", "choice-row__button", choice.label);
      button.type = "button";
      button.dataset.value = choice.value;
      button.addEventListener("click", () => {
        changeSetting(setting.key, choice.value);
        markChosen();
      });
      buttonRow.append(button);
    }
    function markChosen() {
      for (const button of buttonRow.children) {
        const isChosen = button.dataset.value === widget.settings[setting.key];
        button.classList.toggle("choice-row__button--chosen", isChosen);
        button.setAttribute("aria-pressed", String(isChosen));
      }
    }
    markChosen();
    return buttonRow;
  }

  function toggleControl(setting, widget) {
    const checkbox = el("input", "switch");
    checkbox.type = "checkbox";
    checkbox.checked = widget.settings[setting.key];
    checkbox.addEventListener("change", () => changeSetting(setting.key, checkbox.checked));
    return checkbox;
  }

  function textControl(setting, widget) {
    const input = el("input", "field__input");
    input.type = "text";
    input.maxLength = setting.max_length;
    input.value = widget.settings[setting.key];
    input.spellcheck = false;
    input.autocomplete = "off";

    input.addEventListener("input", () => {
      if (setting.uppercase) input.value = input.value.toUpperCase();
      // An empty box is not a valid value. The widget keeps the last good one until the user
      // types something.
      const isEmpty = input.value.trim() === "";
      input.classList.toggle("field__input--invalid", isEmpty);
      if (!isEmpty) changeSetting(setting.key, input.value);
    });
    input.addEventListener("blur", () => {
      input.value = widget.settings[setting.key];
      input.classList.remove("field__input--invalid");
    });
    return input;
  }

  function timeOfDayControl(setting, widget) {
    const input = el("input", "field__input");
    input.type = "time";
    input.value = chosenTimeForOffset(new Date(), widget.settings[setting.key]);
    input.addEventListener("input", () => {
      if (input.value) changeSetting(setting.key, offsetForChosenTime(new Date(), input.value));
    });
    return input;
  }

  function numberControl(setting, widget) {
    const input = el("input", "field__input");
    input.type = "number";
    input.min = setting.min;
    input.max = setting.max;
    input.step = 1;
    input.value = widget.settings[setting.key];
    input.addEventListener("input", () => {
      const number = Number(input.value);
      const isAllowed = input.value !== "" && Number.isInteger(number) && number >= setting.min && number <= setting.max;
      input.classList.toggle("field__input--invalid", !isAllowed);
      if (isAllowed) changeSetting(setting.key, number);
    });
    return input;
  }

  function controlFor(setting, widget) {
    if (setting.kind === "choice") return choiceControl(setting, widget);
    if (setting.kind === "toggle") return toggleControl(setting, widget);
    if (setting.kind === "text") return textControl(setting, widget);
    if (setting.kind === "number" && setting.editor === "time_picker") return timeOfDayControl(setting, widget);
    return numberControl(setting, widget);
  }

  // --- The form -------------------------------------------------------------------------------

  /** The setting's name. Clicking it puts the cursor in the control, where that makes sense. */
  function labelFor(setting, control) {
    const isSingleField = control.tagName === "INPUT" || control.tagName === "SELECT";
    if (!isSingleField) return el("span", "field__label", setting.label);
    control.id = `setting-${setting.key}`;
    const label = el("label", "field__label", setting.label);
    label.htmlFor = control.id;
    return label;
  }

  function changeSetting(key, value) {
    state.changeSetting(key, value);
    showOnlyRowsThatApply();
  }

  /** A setting with "visible_when" is shown only while other settings have the named values. */
  function showOnlyRowsThatApply() {
    const widget = state.selectedWidget();
    if (!widget) return;
    for (const { setting, row } of shownRows) {
      const conditions = Object.entries(setting.visible_when ?? {});
      row.hidden = !conditions.every(([key, value]) => widget.settings[key] === value);
    }
  }

  function rebuild() {
    panelElement.replaceChildren();
    shownRows = [];

    const widget = state.selectedWidget();
    if (!widget) {
      panelElement.append(el("p", "panel__hint", "Click a widget on the display to change its settings."));
      return;
    }

    const catalogWidget = state.catalogWidget(widget.type);
    const title = el("div", "settings__title");
    title.append(
      el("span", "settings__name", catalogWidget.name),
      el("span", "settings__size", widget.size.replace("x", " × ")),
    );
    panelElement.append(title);

    for (const setting of catalogWidget.settings) {
      const row = el("div", `field field--${setting.kind}`);
      row.dataset.settingKey = setting.key;
      const control = controlFor(setting, widget);
      row.append(labelFor(setting, control), control);
      panelElement.append(row);
      shownRows.push({ setting, row });
    }
    if (catalogWidget.settings.length === 0) {
      panelElement.append(el("p", "panel__hint", "This widget has no settings."));
    }
    showOnlyRowsThatApply();

    const removeButton = el("button", "button button--quiet settings__remove");
    removeButton.type = "button";
    removeButton.append(icon("trash"), el("span", "", "Remove widget"));
    removeButton.addEventListener("click", () => state.removeWidget(state.selectedIndex()));
    panelElement.append(removeButton);
  }

  state.subscribe((kindOfChange) => {
    // Not on "settings": rebuilding the form while the user types in it would take the
    // cursor out of the box.
    if (kindOfChange !== "settings" && kindOfChange !== "background") rebuild();
  });
  rebuild();
}
