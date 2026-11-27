"""Draws the six background pictures of the display and saves them as 480x320 JPEG files.

Run it from the web_app folder (it needs the Pillow and numpy packages):

    python3 tools/make_backgrounds.py

The pictures are kept in the repository, so this only has to run again when a picture changes.
The file names must match the "backgrounds" list in data/widget_catalog.json.

The pictures are calm on purpose: soft shapes, no sharp detail, and middle-to-dark tones, so
that white text on top of them stays readable.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SCREEN_WIDTH, SCREEN_HEIGHT = 480, 320

# Everything is drawn four times larger and then shrunk, which smooths the edges.
SCALE = 4
WIDTH, HEIGHT = SCREEN_WIDTH * SCALE, SCREEN_HEIGHT * SCALE

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "static" / "backgrounds"
JPEG_QUALITY = 90

Colour = tuple[int, int, int]


# --- Shared drawing helpers -------------------------------------------------------------------

def vertical_gradient(colour_stops: list[tuple[float, Colour]]) -> Image.Image:
    """A picture that blends from one colour to the next, top to bottom.

    colour_stops lists (position, colour) pairs, with position 0.0 at the top and 1.0 at the
    bottom.
    """
    positions = [position for position, _ in colour_stops]
    row_positions = np.linspace(0.0, 1.0, HEIGHT)
    channels = [
        np.interp(row_positions, positions, [colour[channel] for _, colour in colour_stops])
        for channel in range(3)
    ]
    column = np.stack(channels, axis=1)                        # one colour per row
    pixels = np.repeat(column[:, np.newaxis, :], WIDTH, axis=1)
    return Image.fromarray(pixels.astype(np.uint8), "RGB")


def wavy_line(base_height: float, waves: list[tuple[float, float, float]]) -> list[tuple[float, float]]:
    """Points along a gently rolling line that crosses the picture from left to right.

    base_height is the line's average height (0.0 top, 1.0 bottom). Each wave is
    (how tall, how many times it repeats across the picture, where it starts).
    """
    points = []
    for x in range(0, WIDTH + 1, SCALE):
        across = x / WIDTH
        height = base_height + sum(
            tall * math.sin(2 * math.pi * (repeats * across + start))
            for tall, repeats, start in waves
        )
        points.append((x, height * HEIGHT))
    return points


def fill_below(picture: Image.Image, line: list[tuple[float, float]], colour: Colour) -> None:
    """Paint everything under a line, down to the bottom of the picture."""
    ImageDraw.Draw(picture).polygon(line + [(WIDTH, HEIGHT), (0, HEIGHT)], fill=colour)


def soft_glow(picture: Image.Image, centre: tuple[float, float], radius: float, colour: Colour,
              strength: float) -> Image.Image:
    """Add a blurred disc of light, such as a sun or a moon's halo. strength is 0.0 to 1.0."""
    glow_mask = Image.new("L", (WIDTH, HEIGHT), 0)
    x, y = centre[0] * WIDTH, centre[1] * HEIGHT
    r = radius * HEIGHT
    ImageDraw.Draw(glow_mask).ellipse((x - r, y - r, x + r, y + r), fill=int(255 * strength))
    glow_mask = glow_mask.filter(ImageFilter.GaussianBlur(r * 0.5))
    return Image.composite(Image.new("RGB", (WIDTH, HEIGHT), colour), picture, glow_mask)


def finish(picture: Image.Image, softness: float = 1.5) -> Image.Image:
    """Soften the picture slightly and shrink it to the screen's size."""
    picture = picture.filter(ImageFilter.GaussianBlur(softness * SCALE))
    return picture.resize((SCREEN_WIDTH, SCREEN_HEIGHT), Image.LANCZOS)


# --- The six pictures -------------------------------------------------------------------------

def soft_hills() -> Image.Image:
    """Rolling green hills under a warm evening sky."""
    picture = vertical_gradient([(0.0, (74, 98, 138)), (0.45, (152, 132, 150)), (0.75, (214, 160, 130))])
    picture = soft_glow(picture, centre=(0.72, 0.52), radius=0.20, colour=(250, 214, 165), strength=0.85)
    fill_below(picture, wavy_line(0.62, [(0.05, 1.0, 0.10), (0.02, 2.3, 0.4)]), (104, 128, 122))
    fill_below(picture, wavy_line(0.72, [(0.06, 0.8, 0.55), (0.02, 2.0, 0.1)]), (78, 110, 100))
    fill_below(picture, wavy_line(0.84, [(0.05, 1.2, 0.30), (0.015, 3.1, 0.7)]), (56, 90, 80))
    return finish(picture)


def night_sky() -> Image.Image:
    """A deep blue night with a moon, a few stars and dark hills."""
    picture = vertical_gradient([(0.0, (16, 22, 52)), (0.6, (38, 48, 96)), (1.0, (66, 70, 122))])

    stars = random.Random(7)   # a fixed seed, so the stars are in the same place on every run
    draw = ImageDraw.Draw(picture)
    for _ in range(70):
        x, y = stars.uniform(0, WIDTH), stars.uniform(0, HEIGHT * 0.62)
        size = stars.choice([1.0, 1.0, 1.5, 2.2]) * SCALE
        brightness = stars.randint(150, 235)
        draw.ellipse((x - size, y - size, x + size, y + size), fill=(brightness, brightness, 245))

    picture = soft_glow(picture, centre=(0.78, 0.24), radius=0.16, colour=(150, 160, 215), strength=0.5)
    moon_x, moon_y, moon_radius = 0.78 * WIDTH, 0.24 * HEIGHT, 0.075 * HEIGHT
    ImageDraw.Draw(picture).ellipse(
        (moon_x - moon_radius, moon_y - moon_radius, moon_x + moon_radius, moon_y + moon_radius),
        fill=(236, 236, 250),
    )

    fill_below(picture, wavy_line(0.80, [(0.05, 1.0, 0.25), (0.02, 2.6, 0.6)]), (30, 34, 72))
    fill_below(picture, wavy_line(0.90, [(0.04, 1.4, 0.70), (0.015, 3.0, 0.2)]), (20, 22, 52))
    return finish(picture, softness=0.9)


def calm_sea() -> Image.Image:
    """A quiet sea at dusk, with bands of water getting darker towards the shore."""
    picture = vertical_gradient([(0.0, (58, 110, 138)), (0.5, (128, 176, 184)), (0.56, (176, 204, 198))])
    picture = soft_glow(picture, centre=(0.30, 0.50), radius=0.17, colour=(250, 232, 196), strength=0.8)
    water_bands = [
        (0.56, (88, 150, 162)),
        (0.66, (70, 134, 150)),
        (0.76, (54, 116, 136)),
        (0.87, (40, 98, 120)),
    ]
    for band_number, (height, colour) in enumerate(water_bands):
        waves = [(0.008 + 0.004 * band_number, 2.0 + band_number, 0.2 * band_number), (0.004, 5.0, 0.5)]
        fill_below(picture, wavy_line(height, waves), colour)
    return finish(picture)


def morning_mist() -> Image.Image:
    """Layers of mountains fading into a dusty pink morning."""
    picture = vertical_gradient([(0.0, (122, 110, 140)), (0.5, (184, 148, 158)), (1.0, (206, 170, 160))])
    picture = soft_glow(picture, centre=(0.5, 0.42), radius=0.26, colour=(238, 200, 188), strength=0.6)
    mountain_layers = [
        (0.52, (150, 128, 152), [(0.07, 1.3, 0.05), (0.03, 3.1, 0.3)]),
        (0.64, (122, 106, 138), [(0.08, 0.9, 0.45), (0.03, 2.7, 0.8)]),
        (0.76, (96, 86, 120),   [(0.07, 1.1, 0.80), (0.025, 3.5, 0.1)]),
        (0.89, (72, 66, 100),   [(0.05, 1.5, 0.25), (0.02, 2.9, 0.6)]),
    ]
    for height, colour, waves in mountain_layers:
        fill_below(picture, wavy_line(height, waves), colour)
    return finish(picture, softness=2.2)


def lavender() -> Image.Image:
    """Soft, out-of-focus circles of light on purple."""
    picture = vertical_gradient([(0.0, (96, 82, 148)), (1.0, (150, 112, 164))])
    circles = [
        # centre x, centre y, radius, colour, strength
        (0.18, 0.30, 0.30, (186, 158, 226), 0.80),
        (0.80, 0.22, 0.24, (222, 176, 220), 0.75),
        (0.62, 0.78, 0.34, (104, 86, 170), 0.85),
        (0.30, 0.86, 0.20, (228, 184, 212), 0.65),
        (0.94, 0.70, 0.18, (178, 146, 224), 0.70),
        (0.48, 0.40, 0.14, (232, 204, 234), 0.55),
        (0.05, 0.72, 0.12, (150, 120, 200), 0.60),
        (0.66, 0.10, 0.10, (236, 206, 232), 0.45),
    ]
    for x, y, radius, colour, strength in circles:
        picture = soft_glow(picture, centre=(x, y), radius=radius, colour=colour, strength=strength)
    return finish(picture, softness=1.5)


def forest() -> Image.Image:
    """Rows of pine trees, each row darker and nearer than the one behind it."""
    picture = vertical_gradient([(0.0, (118, 150, 140)), (0.6, (150, 176, 154)), (1.0, (120, 150, 130))])
    picture = soft_glow(picture, centre=(0.5, 0.30), radius=0.30, colour=(206, 220, 190), strength=0.55)

    tree_rows = [
        # where the tree tops are, tree height, tree width, colour
        (0.40, 0.20, 0.060, (98, 132, 120)),
        (0.52, 0.26, 0.075, (72, 108, 98)),
        (0.66, 0.30, 0.095, (48, 84, 76)),
    ]
    trees = random.Random(11)   # a fixed seed, so the trees are in the same place on every run
    draw = ImageDraw.Draw(picture)
    for top, tree_height, tree_width, colour in tree_rows:
        x = -tree_width * trees.random()
        while x < 1.0 + tree_width:
            this_height = tree_height * trees.uniform(0.75, 1.15)
            this_top = top + (tree_height - this_height)
            draw.polygon(
                [
                    ((x - tree_width / 2) * WIDTH, (this_top + this_height) * HEIGHT),
                    (x * WIDTH, this_top * HEIGHT),
                    ((x + tree_width / 2) * WIDTH, (this_top + this_height) * HEIGHT),
                ],
                fill=colour,
            )
            x += tree_width * trees.uniform(0.55, 0.95)
        # The ground the row stands on.
        draw.rectangle((0, (top + tree_height) * HEIGHT - 1, WIDTH, HEIGHT), fill=colour)
    return finish(picture)


BACKGROUNDS = {
    "soft-hills": soft_hills,
    "night-sky": night_sky,
    "calm-sea": calm_sea,
    "morning-mist": morning_mist,
    "lavender": lavender,
    "forest": forest,
}


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for background_id, draw_background in BACKGROUNDS.items():
        output_path = OUTPUT_DIR / f"{background_id}.jpg"
        draw_background().save(output_path, "JPEG", quality=JPEG_QUALITY)
        print(f"{output_path.name}: {output_path.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
