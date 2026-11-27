// The panel's screen for the selected widget: its settings, and "Remove widget" under them.
//
// The form itself is the one the desktop editor uses (editing/widget_settings_form.js). It
// keeps itself in step with the selected widget; this file gives it its place in the panel.

import { el } from "../common/dom.js";
import { setUpWidgetSettingsForm } from "../editing/widget_settings_form.js";
import { topLineWithBack } from "./panel.js";
import { sizeAsText } from "./widget_rows.js";

/** onBack(): let go of the widget and return to the main menu. */
export function createWidgetOptionsScreen({ panel, state, onBack }) {
  // One form for the whole life of the page. It is put into the panel whenever a widget is
  // selected, so a box the user is typing in is never rebuilt under their fingers.
  const form = el("div", "settings");
  setUpWidgetSettingsForm(form, state);

  function show() {
    const widget = state.selectedWidget();
    const catalogWidget = state.catalogWidget(widget.type);
    panel.show("widget-options", {
      top: topLineWithBack({ title: catalogWidget.name, note: sizeAsText(widget.size), onBack }),
      body: [form],
    });
  }

  return { show };
}
