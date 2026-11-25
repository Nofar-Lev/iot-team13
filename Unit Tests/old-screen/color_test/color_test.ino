// Screen test 4: are the colours right, in both ways of drawing?
//
// What it checks
//   That a colour we ask for is the colour the screen shows, in the two ways a program puts
//   pixels on the screen:
//     - fillRect: we name one colour and the library fills an area with it.
//     - pushImage: we hand the library a block of ready-made pixels. This is how pictures,
//       sprites and LVGL send their pixels, so it is the way that matters most later.
//   It also shows whether the panel needs its colours inverted or its red and blue swapped.
//   Run screen test 1 (green_test) first: this test assumes the display itself already works.
//
// What you should see (the screen lies sideways, 480 wide and 320 tall)
//   Row 1, "fillRect:"   eight bars with their names under them: black, red, green, blue,
//                        yellow, cyan, white, grey.
//   Row 2, "pushImage:"  the same eight bars, in the same colours as row 1.
//   Row 3                a strip that goes from black on the left to white on the right. It
//                        should change smoothly, with no sudden jumps.
//
// What we tried, what we found, and the fix
//   Tried:  the first version of this test, which handed pushImage a plain array of 16-bit
//           numbers:
//               tft.pushImage(0, y, 480, 1, line);
//   Found:  row 1 (fillRect) had the right colours. Row 2 (pushImage) had wrong colours,
//           although both rows used the very same eight colour values.
//   Why:    a colour here is a 16-bit number, which is two bytes. When LovyanGFX is handed a
//           plain uint16_t array, it assumes the two bytes of every pixel are stored in the
//           opposite order (the order they travel to the display in). Ours are stored the
//           normal way round, so the library read every pixel with its bytes swapped. By
//           that rule black and white stay right and every other colour changes: red turns
//           blue, green turns red, blue turns green. (Worked out from the rule, not noted
//           from the screen.)
//   Fix:    tell the library what the array really holds, by naming its type:
//               tft.pushImage(0, y, 480, 1, (lgfx::rgb565_t*)line);
//           With this, row 2 shows the same colours as row 1. The values in the array did
//           not change.
//   Also found: the panel needs no inversion and no red/blue swap. Both settings stay false
//           (p.invert and p.rgb_order below).
//   Remember for later: every pixel buffer we fill ourselves and send with pushImage needs
//           this, or the colours come out wrong.
//
// Wiring (module pin -> ESP32 pin), as set in the code below
//   SCK -> 18, SDI (MOSI) -> 23, DC -> 15, CS -> 5, RESET -> 4. GPIO 19 is named as the
//   "data back" pin, but this test reads nothing. The pin numbers are the course's, for the
//   lab's breakout board: see the top of green_test.
//
// Library
//   LovyanGFX, version 1.3.0 (Arduino Library Manager). The tests were run with this version.

// Selects the current version of LovyanGFX's interface. Must come before the include.
#define LGFX_USE_V1
#include <LovyanGFX.hpp>

// Our display, described to the library: which driver chip it has, and which ESP32 pins it is
// wired to.
class LGFX : public lgfx::LGFX_Device {
  lgfx::Panel_ILI9488 _panel;   // the display's driver chip
  lgfx::Bus_SPI _bus;           // the SPI connection that carries the pixels
public:
  LGFX() {
    // --- The SPI connection ---
    auto b = _bus.config();
    b.spi_host = SPI3_HOST;     // which of the ESP32's SPI units to use (VSPI)
    b.freq_write = 40000000;    // speed when sending to the display: 40 MHz
    b.pin_sclk = 18;            // clock
    b.pin_mosi = 23;            // data from the ESP32 to the display
    b.pin_miso = 19;            // data back (not used by this test)
    b.pin_dc   = 15;            // tells the display: command or pixel data
    _bus.config(b);
    _panel.setBus(&_bus);

    // --- The display itself ---
    auto p = _panel.config();
    p.pin_cs  = 5;              // select wire of the display
    p.pin_rst = 4;              // reset: restarts the driver chip
    p.readable   = false;       // the display's SDO is not connected: never read from it
    p.bus_shared = true;        // the touch chip is on the same wires
    // The two settings this test can reveal. Both turned out to be right as they are.
    p.invert    = false;   // if BLACK looks white (all colors "negative"): set true
    p.rgb_order = false;   // if RED and BLUE are swapped: set true
    _panel.config(p);
    setPanel(&_panel);
  }
};

LGFX tft;

// The eight test colours: their short names for the screen, and their values (filled in setup).
const char* NAMES[8] = {"BLK", "RED", "GRN", "BLU", "YEL", "CYN", "WHT", "GRY"};
uint16_t COLORS[8];

void setup() {
  tft.init();
  tft.setRotation(1);   // landscape, 480 x 320
  tft.fillScreen(TFT_BLACK);

  // color565(red, green, blue), each from 0 to 255, gives the 16-bit number for that colour.
  COLORS[0] = tft.color565(0, 0, 0);
  COLORS[1] = tft.color565(255, 0, 0);
  COLORS[2] = tft.color565(0, 255, 0);
  COLORS[3] = tft.color565(0, 0, 255);
  COLORS[4] = tft.color565(255, 255, 0);
  COLORS[5] = tft.color565(0, 255, 255);
  COLORS[6] = tft.color565(255, 255, 255);
  COLORS[7] = tft.color565(128, 128, 128);

  tft.setTextSize(2);
  tft.setTextColor(TFT_WHITE, TFT_BLACK);

  // Row 1: bars drawn with fillRect (the library sends the color directly)
  tft.setCursor(4, 4); tft.print("fillRect:");
  for (int i = 0; i < 8; i++) {
    tft.fillRect(i * 60, 24, 60, 80, COLORS[i]);              // one bar, 60 wide and 80 tall
    tft.setCursor(i * 60 + 12, 108); tft.print(NAMES[i]);     // its name under it
  }

  // Row 2: the same bars drawn from a pixel buffer with pushImage
  // (this is how images, sprites and LVGL send pixels)
  tft.setCursor(4, 136); tft.print("pushImage:");
  static uint16_t line[480];                                  // one row of pixels
  for (int x = 0; x < 480; x++) line[x] = COLORS[x / 60];     // the eight bars, side by side
  // The same row is sent 80 times, one screen line each time. The (lgfx::rgb565_t*) is the
  // fix described at the top of this file.
  for (int y = 156; y < 236; y++) tft.pushImage(0, y, 480, 1, (lgfx::rgb565_t*)line);   // tell the library: normal RGB565 byte order
  for (int i = 0; i < 8; i++) { tft.setCursor(i * 60 + 12, 240); tft.print(NAMES[i]); }

  // Row 3: black-to-white gradient (should be smooth, no sudden jumps)
  for (int x = 0; x < 480; x++) {
    uint8_t v = x * 255 / 479;                                // 0 at the left edge, 255 at the right
    tft.drawFastVLine(x, 268, 48, tft.color565(v, v, v));     // one grey line, 48 tall
  }
}

// Nothing to repeat: the picture stays on the screen.
void loop() {}
