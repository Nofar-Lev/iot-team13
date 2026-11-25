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
```

Every test starts with a comment that says what it checks, how the part is wired, and what
you should see when it works.

## The tests

| Part | Test | What it checks | What you should see |
|---|---|---|---|
| Old Screen ILI9488 | [`old-screen/green_test`](screen/green_test/green_test.ino) | The ESP32 can talk to the display's driver chip (ILI9488) and draw on it | A black screen with one green rectangle |
| Old Screen ILI9488 | [`old-screen/touch_test`](screen/touch_test/touch_test.ino) | The touch chip (XPT2046) reports where the screen is pressed, on the same wires the display uses | A green dot wherever you press, and a `Touch at x=... y=...` line in the Serial Monitor |

Run them in this order. The touch test assumes the display already works.

## How to run a test

1. Install the library the test names at its top. For the screen tests that is **LovyanGFX**,
   from the Arduino IDE's Library Manager.
2. Wire the part as the comment at the top of the test says.
3. Open the test's `.ino` file in the Arduino IDE, choose the ESP32 board and its port, and
   upload.
4. For a test that prints, open the Serial Monitor at 115200 baud.

## Wiring used by the screen tests

The 4-inch display module has the display's driver chip (ILI9488) and a separate touch chip
(XPT2046) on one board. Both are connected over SPI and share the clock and data wires.

| Module pin | ESP32 pin | Used by |
|---|---|---|
| SCK and T_CLK | GPIO 18 | Both tests |
| SDI (MOSI) and T_DIN | GPIO 23 | Both tests |
| DC (RS) | GPIO 15 | Both tests |
| CS | GPIO 5 | Both tests |
| RESET | GPIO 4 | Both tests |
| T_DO | GPIO 19 | Touch test |
| T_CS | GPIO 21 | Touch test |
| SDO (MISO) | not connected | |
| T_IRQ | not connected | |

- **The display's SDO pin stays unconnected on purpose.** The ILI9488 does not let go of that
  wire when it is not selected, so it would talk over the touch chip. Nothing is ever read
  from the display, so only the touch chip's T_DO is connected.
- Power, ground and the backlight (LED) are not set by the tests' code. They have to be wired
  as well.

## Known limits

- The touch test's numbers for translating a press into a screen position are rough guesses,
  so a dot may land beside the press. A calibration step will replace them.
- In the touch test's first version the dot came out mirrored along the screen's long side.
  The test now has `y_min` and `y_max` the other way round, which fixed it.
- Both tests use the screen upright (320 wide, 480 tall). The project will use it sideways
  (480 wide, 320 tall).
