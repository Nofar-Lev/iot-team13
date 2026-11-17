# Unit Tests

A small test program for each hardware part of the device (the screen, the touch layer, each
sensor, the button, the light, the sound), and for each cloud interface.

Each test checks one part on its own. They are also the first tool for finding a faulty part:
run the tests one by one and see which one stops working.

## How the folder is arranged

One folder per hardware part, and inside it one folder per test. Each test is an Arduino
sketch: a folder holding one `.ino` file of the same name, which is the form the Arduino IDE
expects.

```text
Unit Tests/
  screen/
    green_test/green_test.ino
    touch_test/touch_test.ino
    pattern_slides/pattern_slides.ino
    color_test/color_test.ino
    backgrounds/backgrounds.ino
    backgrounds/backgrounds.h            the pictures that the test shows
```

Every test starts with a comment that says what it checks, how the part is wired, and what
you should see when it works. A test that taught us something also says what we tried, what
we found, and what we decided.

## The tests

| Part | Test | What it checks | What you should see |
|---|---|---|---|
| Screen | [`screen/green_test`](screen/green_test/green_test.ino) | The ESP32 can talk to the display's driver chip (ILI9488) and draw on it | A black screen with one green rectangle |
| Screen | [`screen/touch_test`](screen/touch_test/touch_test.ino) | The touch chip (XPT2046) reports where the screen is pressed, on the same wires the display uses | A green dot wherever you press, and a `Touch at x=... y=...` line in the Serial Monitor |
| Screen | [`screen/pattern_slides`](screen/pattern_slides/pattern_slides.ino) | Whether a whole screen can be redrawn fast enough for a sliding animation between screens | Four patterns that slide from one to the next, and the time each slide took in the Serial Monitor |
| Screen | [`screen/color_test`](screen/color_test/color_test.ino) | A colour we ask for is the colour the screen shows, both when the library fills an area (`fillRect`) and when we hand it ready-made pixels (`pushImage`) | Two rows of the same eight colour bars, and a smooth strip from black to white |
| Screen | [`screen/backgrounds`](screen/backgrounds/backgrounds.ino) | How the web app's six background pictures look on the real screen, and whether white text stays readable on them | Each background in turn, with a clock and a date in white over it |

Run `green_test` first: every other test assumes the display already works.

## What the tests taught us

| Test | What we found | What we did about it |
|---|---|---|
| `touch_test` | In its first version, a press appeared mirrored along the screen's long side | The touch chip's range for that side is written the other way round (`y_min` above `y_max`). Nothing else in the code changed |
| `color_test` | In its first version the `fillRect` row had the right colours and the `pushImage` row had wrong ones, from the very same colour values. Handed a plain `uint16_t` array, LovyanGFX assumes the two bytes of every pixel are stored in the opposite order | The array's type is named in the call: `pushImage(..., (lgfx::rgb565_t*)line)`. Every pixel buffer we fill ourselves needs this. The panel needs no inversion and no red/blue swap |
| `backgrounds` | Overall the backgrounds look good. Two lose something: the forest looks grey, not green, and the lavender is too bright, with shades that can hardly be told apart. Our guess: this screen does not show muted shades well | Nothing changed yet. Pictures for this screen need stronger colours and clearer steps between shades, and each one should be looked at on the real screen |
| `pattern_slides` | The picture arrives intact at 20, 27 and 40 MHz, but a full-screen slide is redrawn too slowly: the motion flickers and does not look good (judged by eye). One frame is 480 x 320 x 3 = 460,800 bytes, which takes the wire about 0.09 to 0.18 seconds at these speeds, so 5 to 11 frames a second at most | No sliding and no scrolling animations of large areas. The device switches between screens at once |

## How to run a test

1. Install the library the test names at its top. For the screen tests that is **LovyanGFX**,
   from the Arduino IDE's Library Manager. The tests were run with version 1.3.0.
2. Wire the part as the comment at the top of the test says.
3. Open the test's `.ino` file in the Arduino IDE, choose the ESP32 board and its port, and
   upload.
4. For a test that prints, open the Serial Monitor at 115200 baud.

## Wiring used by the screen tests

The 4-inch display module has the display's driver chip (ILI9488) and a separate touch chip
(XPT2046) on one board. Both are connected over SPI and share the clock and data wires.

The display sits on the lab's breakout board, which connects it to a regular ESP32 DevKit V1.
The pin numbers below are the course's table for that board: the deck "Graphical display for
microcontrollers", slide 8, "ICST Lab's Custom Breakout board" (version of November 2026).

| Module pin | ESP32 pin | Used by |
|---|---|---|
| SCK and T_CLK | GPIO 18 | All the tests |
| SDI (MOSI) and T_DIN | GPIO 23 | All the tests |
| DC (RS) | GPIO 15 | All the tests |
| CS | GPIO 5 | All the tests |
| RESET | GPIO 4 | All the tests |
| T_DO | GPIO 19 | `touch_test` and `backgrounds` read touches; `pattern_slides` sets touch up without using it |
| T_CS | GPIO 21 | `touch_test` and `backgrounds` read touches; `pattern_slides` sets touch up without using it |
| SDO (MISO) | not connected | |
| T_IRQ | not connected | |

- **The display's SDO pin stays unconnected on purpose.** The ILI9488 does not let go of that
  wire when it is not selected, so it would talk over the touch chip. On the lab's breakout
  board that line is cut. Nothing is ever read from the display, so only the touch chip's
  T_DO reaches GPIO 19.
- **Power**, as the same slide says: a wire from the ESP32's VIN (5V) to the breakout board's
  pin marked with an up arrow. The slide does not recommend the pin marked "3v".

## Known limits

- The touch test's numbers for translating a press into a screen position are rough guesses,
  so a dot may land beside the press. A calibration step will replace them.
- `green_test` and `touch_test` use the screen upright (320 wide, 480 tall). The other tests
  use it sideways (480 wide, 320 tall), as the project will.
- `pattern_slides` sends its patterns without the fix that `color_test` describes, so its
  colours on the screen are not the ones its comments name. Its result is about speed and
  does not depend on them.
