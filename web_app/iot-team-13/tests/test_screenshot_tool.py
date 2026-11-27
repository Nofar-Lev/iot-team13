"""The tool that takes the documents' screenshots (tools/take_screenshots.py).

Taking the pictures needs a browser and half a minute, and is done by hand when something in
them changes. These tests only check what can go wrong quietly: a set that is listed but
cannot be loaded, or one that would save its pictures outside the repository.
"""
import sys
from pathlib import Path

WEB_APP_DIR = Path(__file__).resolve().parent.parent   # web_app/iot-team-13
REPOSITORY_DIR = WEB_APP_DIR.parent.parent
sys.path.insert(0, str(WEB_APP_DIR / "tools"))

import take_screenshots  # noqa: E402


def test_there_is_at_least_one_set_of_screenshots():
    assert "one_editor_at_a_time" in take_screenshots.SETS


def test_every_set_says_where_its_pictures_go_and_how_to_take_them():
    for name, screenshot_set in take_screenshots.SETS.items():
        folder = (REPOSITORY_DIR / screenshot_set.PICTURES_FOLDER).resolve()
        assert REPOSITORY_DIR in folder.parents, f"{name} would save outside the repository"
        assert callable(screenshot_set.take), name


def test_the_pictures_of_every_set_go_to_a_folder_of_their_own():
    folders = [screenshot_set.PICTURES_FOLDER for screenshot_set in take_screenshots.SETS.values()]
    assert len(folders) == len(set(folders))


def test_the_sets_can_be_listed_without_a_browser(capsys):
    assert take_screenshots.main(["--list"]) == 0
    assert capsys.readouterr().out.split() == list(take_screenshots.SETS)


def test_a_set_that_does_not_exist_is_refused_and_the_real_ones_are_named(capsys):
    assert take_screenshots.main(["no_such_set"]) == 2
    said = capsys.readouterr().out
    assert "no_such_set" in said and "one_editor_at_a_time" in said
