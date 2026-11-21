# web_app

The web app that manages the smart screen, and the server code behind it.

This is the first working piece: a **display editor**. The user decides what the device shows
by dragging widgets onto a picture of its screen, and the device redraws when they press Save.
There is no hardware yet, so a web page plays the part of the device.

## What is in it

| Page | Address | What it is |
|---|---|---|
| Home | `/` | A picture of what the display shows now, whether the display is connected, and an Edit button. Its other sections are marked **Sample**: they show example data and are not built yet |
| Editor | `/editor` | The display on a 6x4 grid. Drag widgets from the list, move them, change their settings, choose a background per screen, add and remove screens, then Save. A desktop browser gets the desktop editor. A phone gets the phone editor, which is being built: so far it shows the display and moves between its screens |
| Device | `/device` | A stand-in for the real display, meant for a phone held sideways. It redraws by itself when a layout is saved, and a small icon shows whether it is connected |

What is real and what is not:

- **Real:** the editor, saving, the live update of the device page, the connection state, the
  clock and the date.
- **Example data:** the weather, the stock price, the exchange rates, the room's temperature
  and humidity, and the reminders. All of it comes from one file, `data/demo_data.json`.
  The settings are real: the city, the stock symbol and the units that the user picks are
  saved and shown.

## Run it

You need Python 3.9 or newer. Nothing else: the pages need no build step.

On Windows, in this folder:

```
py -m pip install -r requirements.txt
py run_server.py --port 23634
```

On Linux or macOS, use `python3` in place of `py`.

**The port must be given every time; there is no default.** Any free number from 1024 to
65535 will do, and it does not have to be the same from one run to the next. Without
`--port` the server does not start and says how to choose one. If the chosen port is taken,
it says that too and suggests another.

Then open `http://localhost:<port>` on the same computer (http://localhost:23634 for the
command above). Stop the server with Ctrl+C.

**The device page on a phone.** The phone must be on a network that reaches the computer.
When the server starts it prints the addresses to try, in the form
`http://<the computer's address>:<port>/device`. The first time, Windows Firewall may ask
whether Python may accept connections; the phone cannot reach the server until that is allowed.

**Who can open it.** There is no sign-in. While the server runs, anyone who can reach the
computer on the server's port can open the pages and change the layout, so run it on a network you
trust. To accept connections from one network only, give the computer's address on that
network:

```
py run_server.py --port 23634 --host 192.168.1.20
```

The server then answers on that address only. `http://localhost:23634` stops working, even on
the same computer: open `http://192.168.1.20:23634` there too. The server prints the addresses
that work when it starts.

**Starting over.** The saved layout is kept in `data/saved_layout.json` (not in the
repository). Delete that file to go back to the layout the app starts with.

## How it fits together

- **The layout** is a small piece of JSON: which screens exist, which background each has, and
  which widgets sit where, with which settings. Positions are in grid cells, not pixels. The
  editor produces it, the server checks and stores it, and the device draws it. It is the
  agreement between the web side and the device side; `data/default_layout.json` is an example.
- **The widget catalog** (`data/widget_catalog.json`) is the single place that says which
  widgets exist, in which sizes, with which settings. The editor's list, the settings form and
  the server's checks are all built from it.
- **One drawing module** (`static/js/display/`) turns a layout into a picture of the display.
  The editor, the home page and the device page all use it, so they always agree.
- **The server checks every layout before saving it** (`server/layout_validation.py`): inside
  the grid, no overlaps, only known widgets, sizes, backgrounds and settings. The editor does
  not let the user break these rules, and the server checks anyway, because the saved layout
  is what the device will trust.
- **The live channel** (`/api/events`) is one connection that a page keeps open. The server
  pushes news down it: "a layout was saved", "the display went online or offline". Nothing
  polls.

### To add a widget

1. Describe it in `data/widget_catalog.json`: its name, sizes and settings.
2. Write its drawing file in `static/js/display/widgets/`, and its styles in
   `static/css/display.css`.
3. Add one line to `static/js/display/widgets/index.js`.

The editor's list, the settings form and the server's checks pick it up from the catalog.

## The server's addresses

| Address | What it does |
|---|---|
| `/`, `/editor`, `/device` | The three pages. `/editor` is the desktop editor or the phone editor, by the kind of browser; `/editor?view=phone` and `/editor?view=desktop` choose by hand |
| `/static/...` | The files the pages load |
| `GET /api/catalog` | The widget catalog: widgets, grid, backgrounds |
| `GET /api/layout` | The saved layout, its revision number and when it was saved |
| `PUT /api/layout` | Checks a layout. Saves it and tells the connected pages, or answers with what is wrong |
| `GET /api/events?role=device` | The live channel. `role` is `device`, `home` or `editor` |
| `GET /api/demo-data` | The example values |

## What is where

| Folder or file | What it holds |
|---|---|
| `run_server.py` | Starts the server |
| `server/` | The server's code, one file per job |
| `data/widget_catalog.json` | The widgets, the grid and the backgrounds |
| `data/default_layout.json` | The layout shown before anything was saved |
| `data/demo_data.json` | **Example data only.** Stands in for the real data sources until they exist |
| `static/home.html`, `editor.html`, `editor_phone.html`, `device.html` | The pages. The editor has two: one for a desktop, one for a phone |
| `static/css/` | Styles: `display.css` for the display and its widgets, `base.css` for what the pages share, and one file per page |
| `static/js/common/` | Shared by the pages: talking to the server, the live channel, grid arithmetic, icons |
| `static/js/display/` | The drawing module, with one file per widget in `widgets/` |
| `static/js/editing/` | The rules of editing a layout, shared by the desktop editor and the phone editor |
| `static/js/editor/` | The desktop editor: the widget list, dragging, screens, settings, backgrounds, saving |
| `static/js/editor_phone/` | The phone editor: the start screen and full screen, the preview, moving between screens, the panel and its main menu |
| `static/js/device/` | The device page: connection icon, switching screens, full screen |
| `static/js/home/` | The home page: the display card (real) and the sample sections |
| `static/backgrounds/` | The six background pictures, 480x320 |
| `static/fonts/` | The display's font, Outfit, with its licence (SIL Open Font License) |
| `tools/make_backgrounds.py` | The script that drew the backgrounds (needs Pillow and numpy; only run it to change a picture) |
| `tests/` | Tests for the server, and tests that drive the pages in a browser, as a desktop and as a phone (`browser_fixtures.py` holds what they share) |
| `js_tests/` | Tests for the logic of the pages: the grid, the editor's state, time and units |
| `package.json` | Only tells Node that the `.js` files are modules. There are no packages to install |

## Run the tests

```
py -m pip install pytest
py -m pytest
```

That runs three kinds of test:

- **The server's tests.** Always run.
- **The pages' logic tests** (`js_tests/`). They need Node.js and are skipped without it.
  They can also be run alone: `node --test js_tests/`.
- **Tests that use the pages in a real browser**: dragging, saving, watching the device page
  redraw, stopping and restarting the server, and the home page opened as a phone, upright and
  sideways. They need Playwright and are skipped without it:

  ```
  py -m pip install playwright
  py -m playwright install chromium
  ```

The tests save only into a temporary folder. The browser tests start the server on this
computer only, and nothing reaches the internet.
