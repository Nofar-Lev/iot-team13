"""Every rule a layout must follow, each tried with a layout that breaks it."""
import copy

import pytest

from server.layout_validation import validate_layout


def first_widget(layout):
    return layout["screens"][0]["widgets"][0]


def small_clock(column, row):
    return {
        "type": "clock",
        "size": "2x1",
        "col": column,
        "row": row,
        "settings": {"format": "24h", "show_seconds": False, "time_mode": "automatic", "offset_minutes": 0},
    }


def assert_one_problem_mentioning(problems, *words):
    assert len(problems) == 1, problems
    for word in words:
        assert word in problems[0], problems[0]


# --- Layouts that are good -------------------------------------------------------------------

def test_the_default_layout_is_good(default_layout, catalog):
    assert validate_layout(default_layout, catalog) == []


def test_a_small_layout_is_good(one_clock_layout, catalog):
    assert validate_layout(one_clock_layout, catalog) == []


def test_a_screen_with_no_widgets_is_good(one_clock_layout, catalog):
    one_clock_layout["screens"][0]["widgets"] = []
    assert validate_layout(one_clock_layout, catalog) == []


def test_widgets_side_by_side_do_not_overlap(one_clock_layout, catalog):
    one_clock_layout["screens"][0]["widgets"] = [small_clock(0, 0), small_clock(2, 0), small_clock(0, 1)]
    assert validate_layout(one_clock_layout, catalog) == []


def test_a_widget_may_touch_the_far_edges(one_clock_layout, catalog):
    one_clock_layout["screens"][0]["widgets"] = [small_clock(4, 3)]
    assert validate_layout(one_clock_layout, catalog) == []


def test_the_same_cells_may_be_used_on_different_screens(one_clock_layout, catalog):
    one_clock_layout["screens"].append(copy.deepcopy(one_clock_layout["screens"][0]))
    assert validate_layout(one_clock_layout, catalog) == []


def test_the_largest_number_of_screens_is_allowed(one_clock_layout, catalog):
    screen = one_clock_layout["screens"][0]
    one_clock_layout["screens"] = [copy.deepcopy(screen) for _ in range(catalog.max_screens)]
    assert validate_layout(one_clock_layout, catalog) == []


# --- The layout as a whole -------------------------------------------------------------------

@pytest.mark.parametrize("not_a_layout", [None, [], "layout", 7, True])
def test_the_layout_must_be_an_object(not_a_layout, catalog):
    assert validate_layout(not_a_layout, catalog) == ["The layout must be an object."]


@pytest.mark.parametrize("version", [0, 2, "1", None])
def test_the_version_must_be_the_known_one(one_clock_layout, catalog, version):
    one_clock_layout["version"] = version
    assert_one_problem_mentioning(validate_layout(one_clock_layout, catalog), "version")


def test_a_missing_version_is_a_problem(one_clock_layout, catalog):
    del one_clock_layout["version"]
    assert_one_problem_mentioning(validate_layout(one_clock_layout, catalog), "version")


@pytest.mark.parametrize("grid", [{"columns": 8, "rows": 4}, {"columns": 6, "rows": 5}, {"columns": 6}, None, "6x4"])
def test_the_grid_must_match_the_catalog(one_clock_layout, catalog, grid):
    one_clock_layout["grid"] = grid
    assert_one_problem_mentioning(validate_layout(one_clock_layout, catalog), "grid")


def test_an_unknown_field_in_the_layout_is_a_problem(one_clock_layout, catalog):
    one_clock_layout["theme"] = "dark"
    assert_one_problem_mentioning(validate_layout(one_clock_layout, catalog), "unknown field", "theme")


# --- Screens ---------------------------------------------------------------------------------

@pytest.mark.parametrize("screens", [None, {}, "screens"])
def test_screens_must_be_a_list(one_clock_layout, catalog, screens):
    one_clock_layout["screens"] = screens
    assert_one_problem_mentioning(validate_layout(one_clock_layout, catalog), "list of screens")


def test_there_must_be_at_least_one_screen(one_clock_layout, catalog):
    one_clock_layout["screens"] = []
    assert_one_problem_mentioning(validate_layout(one_clock_layout, catalog), "between 1 and")


def test_there_cannot_be_too_many_screens(one_clock_layout, catalog):
    screen = one_clock_layout["screens"][0]
    one_clock_layout["screens"] = [copy.deepcopy(screen) for _ in range(catalog.max_screens + 1)]
    assert_one_problem_mentioning(validate_layout(one_clock_layout, catalog), "between 1 and")


def test_a_screen_must_be_an_object(one_clock_layout, catalog):
    one_clock_layout["screens"] = ["screen"]
    assert_one_problem_mentioning(validate_layout(one_clock_layout, catalog), "Screen 1", "object")


@pytest.mark.parametrize("background", ["no-such-background", "", None, 3, ["soft-hills"]])
def test_the_background_must_be_in_the_list(one_clock_layout, catalog, background):
    one_clock_layout["screens"][0]["background"] = background
    assert_one_problem_mentioning(validate_layout(one_clock_layout, catalog), "Screen 1", "background")


def test_a_screen_must_have_a_list_of_widgets(one_clock_layout, catalog):
    one_clock_layout["screens"][0]["widgets"] = None
    assert_one_problem_mentioning(validate_layout(one_clock_layout, catalog), "Screen 1", "list of widgets")


def test_an_unknown_field_in_a_screen_is_a_problem(one_clock_layout, catalog):
    one_clock_layout["screens"][0]["name"] = "Home"
    assert_one_problem_mentioning(validate_layout(one_clock_layout, catalog), "Screen 1", "unknown field")


def test_a_problem_names_the_screen_it_is_on(one_clock_layout, catalog):
    second_screen = copy.deepcopy(one_clock_layout["screens"][0])
    second_screen["background"] = "no-such-background"
    one_clock_layout["screens"].append(second_screen)
    assert_one_problem_mentioning(validate_layout(one_clock_layout, catalog), "Screen 2")


# --- Widgets: type, size and place -----------------------------------------------------------

def test_a_widget_must_be_an_object(one_clock_layout, catalog):
    one_clock_layout["screens"][0]["widgets"] = ["clock"]
    assert_one_problem_mentioning(validate_layout(one_clock_layout, catalog), "widget 1", "object")


@pytest.mark.parametrize("widget_type", ["sundial", "", None, 5, ["clock"]])
def test_the_widget_type_must_be_in_the_catalog(one_clock_layout, catalog, widget_type):
    first_widget(one_clock_layout)["type"] = widget_type
    assert_one_problem_mentioning(validate_layout(one_clock_layout, catalog), "widget 1", "no widget of type")


@pytest.mark.parametrize("size", ["2x2", "1x1", "6x4", "big", None, 2])
def test_the_size_must_be_one_of_the_widgets_sizes(one_clock_layout, catalog, size):
    first_widget(one_clock_layout)["size"] = size
    assert_one_problem_mentioning(validate_layout(one_clock_layout, catalog), "clock", "size")


@pytest.mark.parametrize("column, row", [("0", 0), (0, None), (1.5, 0), (True, 0), (0, False)])
def test_col_and_row_must_be_whole_numbers(one_clock_layout, catalog, column, row):
    first_widget(one_clock_layout).update(col=column, row=row)
    assert_one_problem_mentioning(validate_layout(one_clock_layout, catalog), "whole numbers")


@pytest.mark.parametrize("column, row", [(-1, 0), (0, -1), (5, 0), (6, 0), (0, 4), (4, 4)])
def test_a_widget_must_fit_inside_the_grid(one_clock_layout, catalog, column, row):
    first_widget(one_clock_layout).update(col=column, row=row)
    assert_one_problem_mentioning(validate_layout(one_clock_layout, catalog), "does not fit inside the grid")


def test_a_large_widget_must_fit_too(one_clock_layout, catalog):
    first_widget(one_clock_layout).update(size="4x2", col=3, row=0)
    assert_one_problem_mentioning(validate_layout(one_clock_layout, catalog), "does not fit inside the grid")


def test_an_unknown_field_in_a_widget_is_a_problem(one_clock_layout, catalog):
    first_widget(one_clock_layout)["colour"] = "red"
    assert_one_problem_mentioning(validate_layout(one_clock_layout, catalog), "widget 1", "unknown field")


# --- Widgets: overlaps -----------------------------------------------------------------------

@pytest.mark.parametrize("column, row", [(0, 0), (1, 0)])
def test_two_widgets_cannot_share_a_cell(one_clock_layout, catalog, column, row):
    one_clock_layout["screens"][0]["widgets"] = [small_clock(0, 0), small_clock(column, row)]
    assert_one_problem_mentioning(validate_layout(one_clock_layout, catalog), "widget 2", "overlaps", "widget 1")


def test_a_large_widget_overlapping_two_others_reports_both(one_clock_layout, catalog):
    large_clock = small_clock(1, 0)
    large_clock["size"] = "4x2"
    one_clock_layout["screens"][0]["widgets"] = [small_clock(0, 0), small_clock(4, 1), large_clock]
    problems = validate_layout(one_clock_layout, catalog)
    assert len(problems) == 2
    assert all("widget 3" in problem and "overlaps" in problem for problem in problems)


# --- Widgets: settings -----------------------------------------------------------------------

@pytest.mark.parametrize("settings", [None, [], "settings"])
def test_settings_must_be_an_object(one_clock_layout, catalog, settings):
    first_widget(one_clock_layout)["settings"] = settings
    assert_one_problem_mentioning(validate_layout(one_clock_layout, catalog), "settings object")


def test_a_missing_setting_is_a_problem(one_clock_layout, catalog):
    del first_widget(one_clock_layout)["settings"]["format"]
    assert_one_problem_mentioning(validate_layout(one_clock_layout, catalog), "format", "missing")


def test_an_unknown_setting_is_a_problem(one_clock_layout, catalog):
    first_widget(one_clock_layout)["settings"]["colour"] = "red"
    assert_one_problem_mentioning(validate_layout(one_clock_layout, catalog), "unknown field", "colour")


@pytest.mark.parametrize(
    "key, bad_value",
    [
        ("format", "36h"),          # a choice that is not offered
        ("format", None),
        ("show_seconds", "yes"),    # a toggle must be true or false
        ("show_seconds", 1),
        ("offset_minutes", 1441),   # a number above its largest value
        ("offset_minutes", -1441),
        ("offset_minutes", 2.5),
        ("offset_minutes", "30"),
        ("offset_minutes", True),
    ],
)
def test_a_setting_value_must_be_allowed(one_clock_layout, catalog, key, bad_value):
    first_widget(one_clock_layout)["settings"][key] = bad_value
    assert_one_problem_mentioning(validate_layout(one_clock_layout, catalog), key, "not allowed")


@pytest.mark.parametrize("city", ["", "   ", "x" * 25, None, 5])
def test_a_text_setting_must_be_non_empty_text_within_its_length(one_clock_layout, catalog, city):
    one_clock_layout["screens"][0]["widgets"] = [
        {"type": "weather", "size": "2x1", "col": 0, "row": 0, "settings": {"city": city, "units": "celsius"}}
    ]
    assert_one_problem_mentioning(validate_layout(one_clock_layout, catalog), "city", "not allowed")


def test_a_text_setting_at_its_longest_is_good(one_clock_layout, catalog):
    one_clock_layout["screens"][0]["widgets"] = [
        {"type": "weather", "size": "2x1", "col": 0, "row": 0, "settings": {"city": "x" * 24, "units": "celsius"}}
    ]
    assert validate_layout(one_clock_layout, catalog) == []


def test_a_widget_with_no_settings_takes_an_empty_settings_object(one_clock_layout, catalog):
    one_clock_layout["screens"][0]["widgets"] = [
        {"type": "reminders", "size": "4x2", "col": 0, "row": 0, "settings": {}}
    ]
    assert validate_layout(one_clock_layout, catalog) == []


# --- Several problems at once ----------------------------------------------------------------

def test_every_problem_is_reported_not_only_the_first(one_clock_layout, catalog):
    one_clock_layout["version"] = 9
    one_clock_layout["screens"][0]["background"] = "no-such-background"
    first_widget(one_clock_layout)["col"] = 5
    assert len(validate_layout(one_clock_layout, catalog)) == 3
