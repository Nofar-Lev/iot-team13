"""The background pictures listed in the catalog exist, and are the size of the screen."""
import pytest

SCREEN_SIZE = (480, 320)


def test_every_background_in_the_catalog_has_its_picture(catalog, config):
    backgrounds_dir = config.static_dir / "backgrounds"
    for background in catalog.raw["backgrounds"]:
        picture_path = backgrounds_dir / background["file"]
        assert picture_path.is_file(), f"{background['id']}: {picture_path.name} is missing"
        assert picture_path.stat().st_size > 0


def test_there_is_no_picture_that_the_catalog_does_not_list(catalog, config):
    listed = {background["file"] for background in catalog.raw["backgrounds"]}
    on_disk = {path.name for path in (config.static_dir / "backgrounds").iterdir()}
    assert on_disk == listed


def test_every_background_is_the_size_of_the_screen(catalog, config):
    pillow_image = pytest.importorskip("PIL.Image", reason="needs the Pillow package to read picture sizes")
    for background in catalog.raw["backgrounds"]:
        with pillow_image.open(config.static_dir / "backgrounds" / background["file"]) as picture:
            assert picture.size == SCREEN_SIZE, background["id"]
