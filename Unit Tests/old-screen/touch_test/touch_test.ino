// Screen test 2: does the touch layer report where the screen is pressed?
//
// What it checks
//   That the touch chip (XPT2046, resistive: it needs a real press, not a light tap) answers
//   over SPI, on the same wires the display uses, and that the two do not disturb each other.
//   Run screen test 1 (green_test) first: this test assumes the display itself already works.
//
// What you should see
//   A black screen. Wherever you press, a small green dot appears and stays. The Serial
//   Monitor (115200 baud) prints a line for every reading:  Touch at x=123 y=456
//   The dot may not land exactly under the press. The numbers that translate the touch
//   chip's readings into screen positions are rough guesses for now (x_min, x_max, y_min,
//   y_max below); a calibration step replaces them later.
//
// What we tried, what we found, and the fix
//   Tried:  the first version of this test, with the touch chip's range written the usual way
//           round on both sides of the screen:
//               x_min = 300, x_max = 3900
//               y_min = 300, y_max = 3900
//   Found:  touch worked, but the dot appeared mirrored along the screen's long side (left
//           and right, when the screen lies sideways): a press near one end drew the dot
//           near the other end.
//   Why:    as we understand it, the touch layer's long side counts in the opposite
//           direction to the display's: where the display's y is smallest, the touch chip
//           reports its largest number.
//   Fix:    y_min and y_max are written the other way round (y_min = 3900, y_max = 300), so
//           the library flips that side. The short side (x) needed no change.
//
// Wiring (module pin -> ESP32 pin), as set in the code below
//   Display:
//     SCK         -> GPIO 18
//     SDI (MOSI)  -> GPIO 23
//     DC (RS)     -> GPIO 15
//     CS          -> GPIO 5
//     RESET       -> GPIO 4
//     SDO (MISO)  -> not connected (see the note below)
//   Touch:
//     T_CLK       -> GPIO 18   (shared with the display's SCK)
//     T_DIN       -> GPIO 23   (shared with the display's SDI)
//     T_DO        -> GPIO 19
//     T_CS        -> GPIO 21
//     T_IRQ       -> not connected: the test asks the touch chip again and again instead
// Where the pin numbers come from
//   The display sits on the lab's breakout board, which connects it to a regular ESP32
//   DevKit V1 board. The pin numbers are the ones in the course's table for that board:
//   the deck "Graphical display for microcontrollers" (in the knowledge bank: "Graphical
//   display on an external screen"), slide 8, "ICST Lab's Custom Breakout board", in the
//   version of November 2026.
//   Power, as that slide says: a wire from the ESP32's VIN (5V) to the breakout board's pin
//   marked with an up arrow. The slide does not recommend the pin marked "3v".
//
// Why the display's SDO stays unconnected
//   The ILI9488 does not let go of the "data back" wire when it is not selected, so it would
//   talk over the touch chip. On the lab's breakout board the display's SDO line is cut for
//   this reason. We never read from the display, so only the touch chip's T_DO reaches
//   GPIO 19.
//
// Library
//   LovyanGFX, version 1.3.0 (Arduino Library Manager). The tests were run with this version.

// Selects the current version of LovyanGFX's interface. Must come before the include.
#define LGFX_USE_V1
#include <LovyanGFX.hpp>

// Our display and its touch layer, described to the library: which chips they have, and which
// ESP32 pins they are wired to.
class LGFX : public lgfx::LGFX_Device {
  lgfx::Panel_ILI9488 _panel;   // the display's driver chip
  lgfx::Bus_SPI _bus;           // the SPI connection that carries the pixels
  lgfx::Touch_XPT2046 _touch;   // the touch chip
public:
  LGFX() {
    // --- The SPI connection ---
    auto b = _bus.config();
    b.spi_host = SPI3_HOST;     // which of the ESP32's SPI units to use (the one called VSPI)
    b.freq_write = 20000000;    // speed when sending to the display: 20 MHz
    b.pin_sclk = 18;            // clock
    b.pin_mosi = 23;            // data from the ESP32 to the display and to the touch chip
    b.pin_miso = 19;   // needed now: touch sends data back on this line
    b.pin_dc   = 15;            // tells the display whether a byte is a command or pixel data
    _bus.config(b);
    _panel.setBus(&_bus);

    // --- The display itself ---
    auto p = _panel.config();
    p.pin_cs  = 5;              // select: the ESP32 pulls it low to talk to the display
    p.pin_rst = 4;              // reset: restarts the driver chip
    p.readable   = false;  // display's SDO is cut   (so the library must never try to read from it)
    p.bus_shared = true;   // touch shares the bus   (so the library lets go of it between uses)
    _panel.config(p);

    // --- The touch chip ---
    auto t = _touch.config();
    t.spi_host = SPI3_HOST;     // the same SPI unit as the display
    t.freq     = 1000000;       // the touch chip is slow: 1 MHz
    t.pin_sclk = 18;            // the same clock wire as the display
    t.pin_mosi = 23;            // the same "data out" wire as the display
    t.pin_miso = 19;            // the touch chip's answers
    t.pin_cs   = 21;            // select wire of the touch chip
    t.pin_int  = -1;            // T_IRQ ("someone is pressing") is not connected
    t.bus_shared = true;        // the display is on the same wires
    // What the touch chip reports at the screen's edges. It measures in its own units,
    // roughly 0 to 4095, and these numbers map them onto the screen.
    t.x_min = 300; t.x_max = 3900;   // rough guesses, calibrate later
    // y runs along the screen's long side. Its two numbers are the other way round on
    // purpose: with min below max, presses along the long side came out mirrored.
    t.y_min = 3900; t.y_max = 300;   // swapped: long side was mirrored
    _touch.config(t);
    _panel.setTouch(&_touch);

    setPanel(&_panel);
  }
};

LGFX tft;

void setup() {
  Serial.begin(115200);        // for the "Touch at ..." lines
  tft.init();                  // start the SPI connection, the display and the touch chip
  tft.fillScreen(TFT_BLACK);   // clear the whole screen
}

void loop() {
  int32_t x, y;
  // getTouch returns true while the screen is pressed, and fills in the screen position.
  if (tft.getTouch(&x, &y)) {
    tft.fillCircle(x, y, 5, TFT_GREEN);            // a dot of radius 5 where it was pressed
    Serial.printf("Touch at x=%d y=%d\n", x, y);
  }
}
