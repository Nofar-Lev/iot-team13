// Screen test 1: does the display show anything at all?
//
// What it checks
//   That the ESP32 can talk to the display's driver chip (ILI9488) over SPI and draw on it.
//   Nothing else is involved: no touch, no Wi-Fi, no sensors.
//
// What you should see
//   A black screen with one green rectangle on it. The screen is used upright here (320 wide,
//   480 tall, because the test sets no rotation). The rectangle is 200 wide and 150 tall, and
//   its top left corner is 60 from the left edge and 100 from the top.
//
// Wiring (display pin -> ESP32 pin), as set in the code below
//   SCK         -> GPIO 18
//   SDI (MOSI)  -> GPIO 23
//   DC (RS)     -> GPIO 15
//   CS          -> GPIO 5
//   RESET       -> GPIO 4
//   SDO (MISO)  -> not connected: this test never reads from the display
//
// Where the pin numbers come from
//   The display sits on the lab's breakout board, which connects it to a regular ESP32
//   DevKit V1 board. The pin numbers are the ones in the course's table for that board:
//   the deck "Graphical display for microcontrollers" (in the knowledge bank: "Graphical
//   display on an external screen"), slide 8, "ICST Lab's Custom Breakout board", in the
//   version of November 2026. "slide 8" in the comments below means that slide.
//   Power, as that slide says: a wire from the ESP32's VIN (5V) to the breakout board's pin
//   marked with an up arrow. The slide does not recommend the pin marked "3v".
//
// Library
//   LovyanGFX, version 1.3.0 (Arduino Library Manager). The tests were run with this version.
//
// If the screen stays black or white
//   Check the wiring against the table above, then try a lower speed in freq_write.

// Selects the current version of LovyanGFX's interface. Must come before the include.
#define LGFX_USE_V1
#include <LovyanGFX.hpp>

// Our display, described to the library: which driver chip it has, and which ESP32 pins it is
// wired to. LovyanGFX has no ready-made description of this module, so we write one.
class LGFX : public lgfx::LGFX_Device {
  lgfx::Panel_ILI9488 _panel;   // the display's driver chip
  lgfx::Bus_SPI _bus;           // the SPI connection that carries the pixels
public:
  LGFX() {
    // --- The SPI connection ---
    auto b = _bus.config();
    b.spi_host = SPI3_HOST;     // which of the ESP32's SPI units to use (the one called VSPI)
    b.freq_write = 20000000;    // speed when sending to the display: 20 MHz
    b.pin_sclk = 18;            // clock
    b.pin_mosi = 23;            // data from the ESP32 to the display
    b.pin_miso = -1;            // data back from the display: not connected
    b.pin_dc   = 15;   // slide 8   (tells the chip whether a byte is a command or pixel data)
    _bus.config(b);
    _panel.setBus(&_bus);

    // --- The display itself ---
    auto p = _panel.config();
    p.pin_cs  = 5;     // slide 8   (select: the ESP32 pulls it low to talk to the display)
    p.pin_rst = 4;              // reset: restarts the driver chip
    _panel.config(p);
    setPanel(&_panel);
  }
};

LGFX tft;

void setup() {
  tft.init();                                    // start the SPI connection and the display
  tft.fillScreen(TFT_BLACK);                     // clear the whole screen
  tft.fillRect(60, 100, 200, 150, TFT_GREEN);    // left, top, width, height, colour
}

// Nothing to repeat: the picture stays on the screen.
void loop() {}
