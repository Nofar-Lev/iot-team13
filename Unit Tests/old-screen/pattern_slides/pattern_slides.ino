// Screen test 3: can the display show a sliding animation between two screens?
//
// What it checks
//   Whether a whole screen can be redrawn fast enough for motion to look smooth. The test
//   slides from one full-screen pattern to the next, the way a phone slides between pages:
//   the old page moves out to the left while the new one comes in from the right, in STEPS
//   frames. Every frame redraws all 480 x 320 pixels.
//   Run screen test 1 (green_test) first: this test assumes the display itself already works.
//
// What you should see
//   Four patterns (rings, a checkerboard, a grid with colour bars, diamonds), with a slide
//   from each to the next every two seconds, in a loop. The patterns have sharp edges and
//   thin lines on purpose, so that a picture that is redrawn too slowly, or damaged on the
//   way, is easy to notice.
//   The Serial Monitor (115200 baud) prints how long each slide took:
//       Slide 1 -> 2: <total> ms total, <per frame> ms per frame
//
// What we tried, what we found, and what we decided
//   Tried:    sliding between full-screen patterns, with the SPI speed (SPI_MHZ) at 20, 27
//             and 40 MHz.
//   Found:    the picture itself arrives intact at all three speeds, but the screen is
//             redrawn too slowly. Each frame is painted from top to bottom while it is
//             visible, so the motion flickers and does not look good. This was judged by
//             eye, which is what matters here; the times the test prints were not written
//             down.
//   Why:      this display takes 3 bytes for every pixel over SPI, so one full frame is
//             480 x 320 x 3 = 460,800 bytes. At 20 MHz the wire alone needs about 0.18
//             seconds for that (0.14 at 27 MHz, 0.09 at 40 MHz), before any time spent
//             working out the pixels. That is at most 5 to 11 frames a second; smooth motion
//             needs about 30. A faster program cannot fix this: the limit is the wire.
//   Decided:  no sliding and no scrolling animations of large areas. When the device
//             switches between screens, the new screen is drawn at once. This is also what
//             the course's display deck advises ("avoid using animated scrolling on large
//             parts of the screen").
//
// Known flaw in this test's colours
//   The patterns are sent with pushImage from a plain uint16_t array, without the fix that
//   color_test describes (naming the array's type as lgfx::rgb565_t*). By what color_test
//   found, the colours on the screen are therefore not the ones named in the comments below.
//   It does not change this test's result: the test is about speed, and the amount of data
//   sent is the same.
//
// Wiring (module pin -> ESP32 pin), as set in the code below
//   The same as screen test 2 (touch_test): SCK and T_CLK -> 18, SDI and T_DIN -> 23,
//   DC -> 15, CS -> 5, RESET -> 4, T_DO -> 19, T_CS -> 21. The display's SDO and T_IRQ are
//   not connected. The touch chip is described to the library so that the wiring can stay
//   as it is, but this test does not read touches.
//   The pin numbers are the course's, for the lab's breakout board: see the top of
//   green_test.
//
// Library
//   LovyanGFX, version 1.3.0 (Arduino Library Manager). The tests were run with this version.

// Selects the current version of LovyanGFX's interface. Must come before the include.
#define LGFX_USE_V1
#include <LovyanGFX.hpp>

// The three settings of the test.
#define SPI_MHZ 20   // looked fine at 20, 27 and 40; drop to 27 if anything looks broken
#define STEPS   12   // frames per slide animation
#define PAGES   4    // how many patterns there are

// Our display and its touch layer, described to the library: which chips they have, and which
// ESP32 pins they are wired to. The same description as in touch_test, except for the speed.
class LGFX : public lgfx::LGFX_Device {
  lgfx::Panel_ILI9488 _panel;   // the display's driver chip
  lgfx::Bus_SPI _bus;           // the SPI connection that carries the pixels
  lgfx::Touch_XPT2046 _touch;   // the touch chip (set up, not used by this test)
public:
  LGFX() {
    // --- The SPI connection ---
    auto b = _bus.config();
    b.spi_host = SPI3_HOST;             // which of the ESP32's SPI units to use (VSPI)
    b.freq_write = SPI_MHZ * 1000000;   // speed when sending to the display, set above
    b.pin_sclk = 18;                    // clock
    b.pin_mosi = 23;                    // data from the ESP32 to the display and the touch chip
    b.pin_miso = 19;                    // data back, from the touch chip only
    b.pin_dc   = 15;                    // tells the display: command or pixel data
    _bus.config(b);
    _panel.setBus(&_bus);

    // --- The display itself ---
    auto p = _panel.config();
    p.pin_cs  = 5;                      // select wire of the display
    p.pin_rst = 4;                      // reset: restarts the driver chip
    p.readable   = false;               // the display's SDO is not connected: never read from it
    p.bus_shared = true;                // the touch chip is on the same wires
    _panel.config(p);

    // --- The touch chip ---
    auto t = _touch.config();
    t.spi_host = SPI3_HOST;
    t.freq     = 1000000;               // the touch chip is slow: 1 MHz
    t.pin_sclk = 18;
    t.pin_mosi = 23;
    t.pin_miso = 19;
    t.pin_cs   = 21;                    // select wire of the touch chip
    t.pin_int  = -1;                    // T_IRQ is not connected
    t.bus_shared = true;
    t.x_min = 300;  t.x_max = 3900;     // rough guesses, as in touch_test
    t.y_min = 3900; t.y_max = 300;      // the other way round on purpose: see touch_test
    _touch.config(t);
    _panel.setTouch(&_touch);

    setPanel(&_panel);
  }
};

LGFX tft;

// One row of pixels, worked out here and then sent to the display in one piece.
// 480 is the screen's width when it lies sideways.
static uint16_t line[480];

// Palette colors, filled in setup()
uint16_t NAVY, CYAN, DKGREEN, LIME, DKGREY, LTGREY, DKRED, TEAL;
uint16_t BARS[6];

// Used only by the page labels, which are switched off in drawFrame() below.
const char* PAGE_NAMES[PAGES] = {"1: rings", "2: checkerboard", "3: grid + color bars", "4: diamonds"};

// Color of one pixel of a page. lx, y = position inside that page.
// The patterns are computed, not stored: a stored full-screen picture would not fit in memory.
static inline uint16_t pagePixel(int page, int lx, int y) {
  int dx = lx - 240, dy = y - 160;   // distance from the page center
  switch (page) {
    case 0:  // Rings: blue and cyan, getting thinner toward the edges
      return ((dx * dx + dy * dy) / 1500) & 1 ? CYAN : NAVY;
    case 1:  // Checkerboard: 40-pixel squares
      return ((lx / 40) + (y / 40)) & 1 ? LIME : DKGREEN;
    case 2:  // Grid of 1-pixel lines every 20 px, color bars at the bottom
      if (y >= 260) return BARS[lx / 80];
      return (lx % 20 == 0 || y % 20 == 0) ? LTGREY : DKGREY;
    default: // Diamonds: red and teal
      return ((abs(dx) + abs(dy)) / 16) & 1 ? TEAL : DKRED;
  }
}

// One animation frame: page "from" shifted left by off, page "to" entering from the right
// off = 0 shows only "from"; off = the screen's width shows only "to".
// The whole screen is redrawn, row by row from the top. This is the slow part.
void drawFrame(int from, int to, int off) {
  const int W = tft.width(), H = tft.height();
  tft.startWrite();   // keep the SPI connection open for the whole frame
  for (int y = 0; y < H; y++) {
    for (int x = 0; x < W; x++) {
      int lx = x + off;   // where this pixel is in the two pages laid side by side
      line[x] = (lx < W) ? pagePixel(from, lx, y) : pagePixel(to, lx - W, y);
    }
    tft.pushImage(0, y, W, 1, line);   // send this one row to the display
  }
  // Switched off: text labels on the pages. The results at the top of this file were seen
  // without them. To bring them back, remove the "//" from the four lines below.
  // Page labels: small text shows corruption easily
  // tft.setTextSize(2);
  // tft.setTextColor(TFT_WHITE, TFT_BLACK);
  // tft.setCursor(16 - off, 16);     tft.print(PAGE_NAMES[from]);
  // tft.setCursor(16 - off + W, 16); tft.print(PAGE_NAMES[to]);
  tft.endWrite();   // close the SPI connection that startWrite() opened above
}

void setup() {
  Serial.begin(115200);
  tft.init();
  tft.setRotation(1);   // landscape, 480 x 320

  // The colours, converted to the 16-bit form the row buffer holds (red, green, blue: 0 to 255).
  NAVY    = tft.color565(10, 25, 60);    CYAN   = tft.color565(40, 200, 230);
  DKGREEN = tft.color565(10, 60, 25);    LIME   = tft.color565(140, 230, 90);
  DKGREY  = tft.color565(25, 25, 30);    LTGREY = tft.color565(200, 200, 200);
  DKRED   = tft.color565(120, 15, 20);   TEAL   = tft.color565(20, 150, 140);
  BARS[0] = tft.color565(220, 40, 40);   BARS[1] = tft.color565(40, 200, 60);
  BARS[2] = tft.color565(40, 90, 230);   BARS[3] = tft.color565(40, 210, 220);
  BARS[4] = tft.color565(240, 220, 40);  BARS[5] = tft.color565(255, 255, 255);

  Serial.printf("\nSPI at %d MHz\n", SPI_MHZ);
  drawFrame(0, 1, 0);   // show page 1
  delay(1500);
}

// Slide to the next page, print how long it took, wait two seconds, and go on.
void loop() {
  static int page = 0;
  int next = (page + 1) % PAGES;

  // Time the whole slide: STEPS frames, each one moved further to the left.
  uint32_t t0 = millis();
  for (int i = 1; i <= STEPS; i++) drawFrame(page, next, tft.width() * i / STEPS);
  uint32_t t = millis() - t0;

  Serial.printf("Slide %d -> %d: %lu ms total, %lu ms per frame\n",
                page + 1, next + 1, (unsigned long)t, (unsigned long)(t / STEPS));
  page = next;
  delay(2000);
}
