// Which screen the panel shows.
//
// The rule:
//   - While a widget is selected, the panel shows that widget's options.
//   - While nothing is selected, it shows the menu that is open: the main menu, or one of the
//     screens reached from it (the list of widgets, a widget's sizes, the backgrounds).
//   - Selecting a widget closes whatever menu was open. So when the widget is let go of, the
//     panel is back at the main menu.

const MAIN_MENU = { name: "main-menu" };

/**
 * state:   the editor's state (editing/editor_state.js).
 * screens: { mainMenu, addWidget, widgetSizes, backgrounds, widgetOptions }. Each has show(),
 *          which fills the panel; widgetSizes.show(widgetType) takes the widget's type.
 */
export function createPanelRouter({ state, screens }) {
  let openMenu = MAIN_MENU;

  function showWhatApplies() {
    if (state.selectedWidget()) {
      openMenu = MAIN_MENU;
      screens.widgetOptions.show();
    } else if (openMenu.name === "add-widget") {
      screens.addWidget.show();
    } else if (openMenu.name === "widget-sizes") {
      screens.widgetSizes.show(openMenu.widgetType);
    } else if (openMenu.name === "backgrounds") {
      screens.backgrounds.show();
    } else {
      screens.mainMenu.show();
    }
  }

  /** Open one of the menu screens. Whatever was selected is let go of. */
  function open(name, details = {}) {
    openMenu = { name, ...details };
    state.selectWidget(null);
    showWhatApplies();
  }

  state.subscribe((kindOfChange) => {
    // Not on "settings": the user is typing in the options, and showing them again would take
    // the cursor out of the box.
    if (kindOfChange !== "settings") showWhatApplies();
  });

  return {
    showWhatApplies,
    openAddWidget: () => open("add-widget"),
    openWidgetSizes: (widgetType) => open("widget-sizes", { widgetType }),
    openBackgrounds: () => open("backgrounds"),
    /** Back to the main menu, letting go of the selected widget. */
    backToMainMenu: () => open(MAIN_MENU.name),
  };
}
