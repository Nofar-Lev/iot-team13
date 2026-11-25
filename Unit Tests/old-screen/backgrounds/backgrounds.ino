// Shows the six background pictures (JPEG) on the display, with white text on top.
// Moves to the next picture every 3 seconds (tapping also skips ahead). Timings go to the Serial Monitor (115200).
//
// backgrounds.h must be in the same folder as this file.
//
// Screen test 5: how do the app's background pictures look on the real screen?
//
// What it checks
//   The six backgrounds are the ones the web app offers for a screen (the files in
//   web_app/static/backgrounds). On the device they will sit behind the widgets. This test
//   shows each one on the real screen, with white text over it in the place and size of a
//   clock and a date, to see three things:
//     - that the ESP32 can unpack a JPEG picture and draw it (drawJpg);
//     - how the colours of each picture come out on this screen;
//     - whether white text stays readable on top of each picture.
//   Run screen test 1 (green_test) first: this test assumes the display itself already works.
//
// What you should see (the screen lies sideways, 480 wide and 320 tall)
//   One background filling the screen, with "12:34" and a date in white over it and the
//   picture's name in the bottom left corner. Every 3 seconds, or when the screen is
//   pressed, the next picture appears. The Serial Monitor (115200 baud) prints a line per
//   picture:   calm-sea      ok    , JPEG decode+draw: <time> ms
//
// What we tried, what we found, and what it means
//   Tried:  all six backgrounds, as they are in the web app, with nothing adjusted for the
//           screen.
//   Found:  overall they look good on the real screen. Two of them lose something:
//             - forest:   it looks grey, not green.
//             - lavender: it is too bright, and its different shades can hardly be told
//                         apart.
//   Why (our guess, not measured): this screen does not show muted shades well. Colours that
//           are only a little different from grey, or from each other, come out the same.
//   What it means: a picture that looks right in a browser is not automatically right on
//           the device. Pictures for this screen need stronger colours and clearer steps
//           between their shades, and each new one should be looked at on the real screen.
//           Nothing was changed in the pictures yet.
//
// Wiring (module pin -> ESP32 pin), as set in the code below
//   The same as screen test 2 (touch_test): SCK and T_CLK -> 18, SDI and T_DIN -> 23,
//   DC -> 15, CS -> 5, RESET -> 4, T_DO -> 19, T_CS -> 21. The pin numbers are the course's,
//   for the lab's breakout board: see the top of green_test.
//
// Library
//   LovyanGFX, version 1.3.0 (Arduino Library Manager). The tests were run with this version.
//   It also unpacks the JPEG pictures; no other library is needed.

// Selects the current version of LovyanGFX's interface. Must come before the include.
#define LGFX_USE_V1
#include <LovyanGFX.hpp>
#include "backgrounds.h"   // the six pictures, as bytes inside the program

// Our display and its touch layer, described to the library: which chips they have, and which
// ESP32 pins they are wired to. The same description as in touch_test, except for the speed.
class LGFX : public lgfx::LGFX_Device {
  lgfx::Panel_ILI9488 _panel;   // the display's driver chip
  lgfx::Bus_SPI _bus;           // the SPI connection that carries the pixels
  lgfx::Touch_XPT2046 _touch;   // the touch chip
public:
  LGFX() {
    // --- The SPI connection ---
    auto b = _bus.config();
    b.spi_host = SPI3_HOST;     // which of the ESP32's SPI units to use (VSPI)
    b.freq_write = 40000000;    // speed when sending to the display: 40 MHz
    b.pin_sclk = 18;            // clock
    b.pin_mosi = 23;            // data from the ESP32 to the display and the touch chip
    b.pin_miso = 19;            // data back, from the touch chip only
    b.pin_dc   = 15;            // tells the display: command or pixel data
    _bus.config(b);
    _panel.setBus(&_bus);

    // --- The display itself ---
    auto p = _panel.config();
    p.pin_cs  = 5;              // select wire of the display
    p.pin_rst = 4;              // reset: restarts the driver chip
    p.readable   = false;       // the display's SDO is not connected: never read from it
    p.bus_shared = true;        // the touch chip is on the same wires
    _panel.config(p);

    // --- The touch chip ---
    auto t = _touch.config();
    t.spi_host = SPI3_HOST;
    t.freq     = 1000000;       // the touch chip is slow: 1 MHz
    t.pin_sclk = 18;
    t.pin_mosi = 23;
    t.pin_miso = 19;
    t.pin_cs   = 21;            // select wire of the touch chip
    t.pin_int  = -1;            // T_IRQ is not connected
    t.bus_shared = true;
    t.x_min = 300;  t.x_max = 3900;   // rough guesses, as in touch_test
    t.y_min = 3900; t.y_max = 300;    // the other way round on purpose: see touch_test
    _touch.config(t);
    _panel.setTouch(&_touch);

    setPanel(&_panel);
  }
};

LGFX tft;

// One background: its name, where its JPEG bytes are, and how many there are.
struct Background { const char* name; const uint8_t* data; size_t size; };
const Background BACKGROUNDS[] = {
  {"calm-sea",     calm_sea_jpg,     sizeof(calm_sea_jpg)},
  {"forest",       forest_jpg,       sizeof(forest_jpg)},
  {"lavender",     lavender_jpg,     sizeof(lavender_jpg)},
  {"morning-mist", morning_mist_jpg, sizeof(morning_mist_jpg)},
  {"night-sky",    night_sky_jpg,    sizeof(night_sky_jpg)},
  {"soft-hills",   soft_hills_jpg,   sizeof(soft_hills_jpg)},
};
const int COUNT = sizeof(BACKGROUNDS) / sizeof(BACKGROUNDS[0]);
int current = 0;   // which background is showing

// Draw background number i with the sample text over it, and print how long the picture took.
void show(int i) {
  // Unpack the JPEG and draw it from the top left corner. Only this part is timed.
  uint32_t t0 = millis();
  bool ok = tft.drawJpg(BACKGROUNDS[i].data, BACKGROUNDS[i].size, 0, 0);
  uint32_t jpgMs = millis() - t0;

  // White text on top, like a clock widget, to check readability
  tft.setTextColor(TFT_WHITE);                // white, with nothing painted behind the letters
  tft.setTextDatum(middle_center);            // the position given is the text's middle
  tft.setFont(&fonts::FreeSansBold24pt7b);
  tft.drawString("12:34", 240, 120);
  tft.setFont(&fonts::FreeSans12pt7b);
  tft.drawString("Tuesday, 17 November", 240, 175);
  tft.setFont(&fonts::FreeSans9pt7b);
  tft.setTextDatum(bottom_left);              // the position given is the text's bottom left
  tft.drawString(BACKGROUNDS[i].name, 8, 312);

  Serial.printf("%-13s %s, JPEG decode+draw: %lu ms\n",
                BACKGROUNDS[i].name, ok ? "ok    " : "FAILED", (unsigned long)jpgMs);
}

void setup() {
  Serial.begin(115200);
  tft.init();
  tft.setRotation(1);   // landscape, 480 x 320
  show(current);
}

// Move to the next picture every 3 seconds, or at once when the screen is pressed.
void loop() {
  static uint32_t lastChange = millis();
  int32_t x, y;
  bool tapped = tft.getTouch(&x, &y);
  if (tapped || millis() - lastChange >= 3000) {
    current = (current + 1) % COUNT;
    show(current);
    lastChange = millis();
    if (tapped) while (tft.getTouch(&x, &y)) delay(10);   // wait until the finger lifts
  }
}
