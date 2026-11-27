# web_app

The web app that manages the smart screen, and the server code behind it.

The first working pieces are the **home page** and the **display editor**. In the editor the
user decides what the device shows by putting widgets onto a picture of its screen, and the
device redraws when they save. The app works in a desktop browser and on a phone. There is no
hardware yet, so a web page plays the part of the device.

The editor can be open in several places, and only one of them is in use at a time. Unsaved
work is kept on the server as a draft, so a closed tab or a lost connection does not lose it.
See "One editor at a time" below.

## What is in it

The whole app is served under one path, `/iot-team-13`, on a laptop and online alike: its home
page is `http://localhost:<port>/iot-team-13/`. The addresses below are inside the app, after
that path. Opening the bare address, `http://localhost:<port>`, forwards to the app.

| Page | Address | What it is |
|---|---|---|
| Home | `/` | A picture of what the display shows now, whether the display is connected, and an Edit button. Its other sections are marked **Sample**: they show example data and are not built yet. One page for a desktop and a phone; it adapts to the window |
| Editor, on a desktop | `/editor` | The display on a 6x4 grid, between a list of widgets and a settings panel. Drag widgets from the list, move them, change their settings, choose a background per screen, add and remove screens, then Save |
| Editor, on a phone | `/editor` | The same editing, in a design of its own for a phone held sideways, in full screen: the display's preview and one panel. See "The editor on a phone" below |
| Device | `/device` | A stand-in for the real display, for a phone held sideways. It redraws by itself when a layout is saved, and a small icon shows whether it is connected. It was made to show the idea before there is hardware, and is not part of the final system |

What is real and what is not:

- **Real:** the two editors, the draft and saving, taking over from another editor, the live
  update of the device page, the connection state, the clock and the date.
- **Example data:** the weather, the stock price, the exchange rates, the room's temperature
  and humidity, and the reminders. All of it comes from one file, `data/demo_data.json`.
  The settings are real: the city, the stock symbol and the units that the user picks are
  saved and shown.

### The editor on a phone

The Edit button of the home page opens it. It starts with "Loading editor...", and then one
button, **Open the editor**: a browser only lets a page go full screen as the answer to a tap.
The tap switches to full screen and turns the picture sideways. If the editor is in use
somewhere else, or unsaved changes were left behind, it asks about that first, before the
button.

| To | Do this |
|---|---|
| Add a widget | Tap **Add widget**, then tap a widget: it lands in the first free place. The clock and the weather ask for a size first. What has no room on this screen is greyed out |
| Put a new widget where you want it | Press and hold it in the list, carry it onto the preview, and let go |
| Change a widget | Tap it on the preview: the panel shows its settings. Tap anywhere else, or Back, to let go of it |
| Move a widget | Press and hold it on the preview until it lifts, carry it, and let go. A green ghost shows where it will land; red means it would overlap another widget |
| Remove a widget | Tap it, then **Remove widget** |
| Move between screens | Swipe the preview sideways, or tap the round arrows on its edges |
| Add a screen | On the last screen, the right arrow is a **+** |
| Remove a screen | **Remove this screen**. It asks for a second tap if the screen has widgets on it |
| Choose a background | **Backgrounds**, then tap one |
| Save | **Save layout**. **Discard** goes back to what was saved, after a second tap |
| Leave | **Home**. With unsaved changes it asks: Keep as draft, Save changes, Discard changes, or Return to the editor |

It was made for Android phones and tried on one. An iPhone's browser gives a page neither full
screen nor a say over rotation: there the editor asks for the phone to be turned, and works
under the browser's bars.

### One editor at a time

Both editors follow the same rules. The reasons for them, with screenshots, are in
`Documentation/web_app_design_decisions/one_editor_at_a_time.md`.

- **Every change goes to the server's draft** as it is made. The device and the home page go
  on showing the saved layout until Save.
- **Only one editor is in use.** A second one that opens takes over at once if the first has
  nothing unsaved; the first is told.
- **If the first has unsaved changes,** the second chooses: take over and continue them, take
  over and discard them, or leave. The first is then asked to approve or refuse, with a
  20-second timer on both sides. No answer counts as approval.
- **A draft that was left behind** (a closed tab, a dead battery) is offered to the next editor
  that opens: resume it or discard it.
- **An editor that loses the server stops,** says so, and offers to reload. It does not
  reconnect by itself. After the reload it is a new editor, by the same rules.
- **Home asks** what should happen to unsaved changes: keep them as a draft, save them, or
  discard them. Closing the tab asks nothing and keeps the draft.

To see it, open `/editor` in two tabs, change something in the first, and look at the second.

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
command above). It forwards to the app, at `http://localhost:23634/iot-team-13/`. Stop the
server with Ctrl+C.

**On a phone.** The phone must be on a network that reaches the computer. When the server
starts it prints this computer's addresses. Open `http://<the computer's address>:<port>` on
the phone for the app, and the same with `/device` at the end for the device page. The first
time, Windows Firewall may ask whether Python may accept connections; the phone cannot reach
the server until that is allowed.

**The phone editor on a computer.** Open `http://localhost:<port>/iot-team-13/editor?view=phone`.
In the same way, `editor?view=desktop` shows the desktop editor on a phone.

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

**Starting over.** The saved layout is kept in `data/saved_layout.json`, and unsaved work in
`data/draft_layout.json` while there is any (neither is in the repository). Stop the server
and delete both files to go back to the layout the app starts with.

## How it fits together

- **One path, and relative addresses.** The app is served under `/iot-team-13`, and that name
  is written in exactly one place: `app_path` in `server/config.py`. The pages, scripts and
  styles never mention it. Every address in them is relative (`static/css/home.css`,
  `api/layout`), never one that starts with a slash, so the app works under any path. An
  address that starts with a slash points at the top of the site, outside the app, and finds
  nothing there. Two things keep this true: a test that reads every page, script and style
  for such an address (`tests/test_addresses_are_relative.py`), and a browser test that tours
  the pages with the app served at four different paths. For the same reason every page sits
  directly under the app's path, never deeper.
- **The layout** is a small piece of JSON: which screens exist, which background each has, and
  which widgets sit where, with which settings. Positions are in grid cells, not pixels. The
  editor produces it, the server checks and stores it, and the device draws it. It is the
  agreement between the web side and the device side; `data/default_layout.json` is an example.
- **The widget catalog** (`data/widget_catalog.json`) is the single place that says which
  widgets exist, in which sizes, with which settings. The editors' lists, the settings form and
  the server's checks are all built from it.
- **One drawing module** (`static/js/display/`) turns a layout into a picture of the display.
  Both editors, the home page and the device page all use it, so they always agree.
- **Two editors, one set of rules.** The desktop editor and the phone editor are separate
  pages, each with its own styles and its own code for arrangement and gestures. No file asks
  "is this a phone?". What they share is only what is exactly the same for both
  (`static/js/editing/`): the rules of editing, the form of a widget's settings, the small
  pictures of widgets, and everything about one editor at a time.
- **The server keeps the rules of one editor at a time** (`server/one_editor_at_a_time.py`):
  which editor is the one in use, the draft, and the take-over with its timer. Only the editor
  in use can change the draft, save or discard, and the server has no other way to save a
  layout, so a page cannot go around the rules.
- **An editor page's part in those rules is the editing session**
  (`static/js/editing/editing_session.js`). It asks to be the editor in use, sends every change
  to the draft one at a time, and tells the page its situation by name ("editing",
  "asked_to_hand_over", "connection_lost"). The messages' wording (`session_messages.js`) and
  the dialog (`dialog.js`) are shared too; each editor only gives the dialog its place.
- **The server chooses the editor** (`server/which_editor.py`). Both are at `/editor`. A
  browser on a phone says so in the label it sends with every request, and gets the phone
  editor; everything else, tablets included, gets the desktop editor.
- **The server checks every layout before saving it** (`server/layout_validation.py`): inside
  the grid, no overlaps, only known widgets, sizes, backgrounds and settings. The editors do
  not let the user break these rules, and the server checks anyway, because the saved layout
  is what the device will trust.
- **The live channel** (`/api/events`) is one connection that a page keeps open. The server
  pushes news down it: "a layout was saved", "the display went online or offline". Nothing
  polls. To the server, an editor is its live channel: it is given its id when the channel
  opens, and is gone when it closes. That is how the server knows whether the other editor is
  still there, and why a reloaded editor counts as a new one.
- **Pictures are kept by browsers.** A browser may keep the background pictures and the font
  for a day, so they are there at once on the next visit. It asks about pages, styles and
  scripts every time, so an edit to one of those shows on the next refresh. For that reason
  **a background picture is never changed in place**: a new version is a new file with a new
  name (`forest-v2.jpg`), the old file is deleted, and the catalog's entry is pointed at the
  new file.

### To add a widget

1. Describe it in `data/widget_catalog.json`: its name, sizes and settings.
2. Write its drawing file in `static/js/display/widgets/`, and its styles in
   `static/css/display.css`.
3. Add one line to `static/js/display/widgets/index.js`.

Both editors' lists, the settings form and the server's checks pick it up from the catalog.

## The server's addresses

All of them are inside the app, after `/iot-team-13`. Outside that path the server answers
only the bare address, which forwards to the app.

| Address | What it does |
|---|---|
| `/`, `/device` | The home page and the device page |
| `/editor` | The desktop editor or the phone editor, by the kind of browser. `/editor?view=phone` and `/editor?view=desktop` choose by hand |
| `/static/...` | The files the pages load |
| `GET /api/catalog` | The widget catalog: widgets, grid, backgrounds |
| `GET /api/layout` | The saved layout, its revision number and when it was saved |
| `GET /api/events?role=device` | The live channel. `role` is `device`, `home` or `editor`. An editor is given its id in the first news |
| `GET /api/demo-data` | The example values |

The addresses an editor calls. Each request carries the editor's id, and one that the rules do
not allow is answered with status 409 and a `reason`:

| Address | What it does |
|---|---|
| `POST /api/editing/enter` | A newly opened editor asks to be the one in use. The answer is its situation: editing (with the saved layout and the draft), a draft that was left behind, another editor with unsaved changes, or a take-over in progress |
| `POST /api/editing/draft-left-behind` | Its choice about a draft it found: resume it or discard it |
| `PUT /api/editing/draft` | The editor in use changed something: the layout as it is now. It is checked like every layout |
| `POST /api/editing/save` | The draft becomes the saved layout, and the connected pages are told |
| `POST /api/editing/discard` | The draft is erased |
| `POST /api/editing/take-over` | Ask the editor in use to hand over, continuing its changes or discarding them |
| `POST /api/editing/take-over/approve`, `.../refuse` | The answer of the editor in use |
| `POST /api/editing/leave` | An editor page is going away |

## What is where

| Folder or file | What it holds |
|---|---|
| `run_server.py` | Starts the server |
| `server/` | The server's code, one file per job |
| `data/widget_catalog.json` | The widgets, the grid and the backgrounds |
| `data/default_layout.json` | The layout shown before anything was saved |
| `data/demo_data.json` | **Example data only.** Stands in for the real data sources until they exist |
| `static/home.html`, `editor.html`, `editor_phone.html`, `device.html` | The pages. The editor has two: one for a desktop, one for a phone |
| `static/css/` | Styles: `display.css` for the display and its widgets, `base.css` for what the pages share, one file per page (`editor.css` for the desktop editor, `editor_phone.css` for the phone editor), and `dialog.css` for the dialog that both editors show |
| `static/js/common/` | Shared by the pages: talking to the server, the live channel, grid arithmetic, icons |
| `static/js/display/` | The drawing module, with one file per widget in `widgets/` |
| `static/js/editing/` | What the two editors share: the rules of editing a layout, the form of a widget's settings, the small pictures of widgets, and one editor at a time (the editing session, the sender that keeps the draft up to date, the messages and their dialog, Save and Discard, and leaving with unsaved changes) |
| `static/js/editor/` | The desktop editor: the widget list, dragging, screens, backgrounds, the Save and Discard buttons |
| `static/js/editor_phone/` | The phone editor, one file per part. `phone_editor_main.js` lists them all: the start screen and full screen, the preview and what a touch on it means (tap, swipe, press and hold), carrying a widget, moving between screens, the panel and its screens |
| `static/js/device/` | The device page: connection icon, switching screens, full screen |
| `static/js/home/` | The home page: the display card (real) and the sample sections |
| `static/backgrounds/` | The six background pictures, 480x320 |
| `static/fonts/` | The display's font, Outfit, with its licence (SIL Open Font License) |
| `tools/make_backgrounds.py` | The script that drew the backgrounds (needs Pillow and numpy). A new version of a picture gets a new file name; see "Pictures are kept by browsers" above |
| `tools/take_screenshots.py`, `tools/screenshots/` | Takes the screenshots that the documents use, from the app itself: see "The documents' screenshots" below |
| `tests/` | Tests for the server, and tests that drive the pages in a browser, as a desktop and as a phone, with one editor and with several at once. `browser_fixtures.py`, `phone_editor_helpers.py` and `live_channel.py` hold what they share |
| `js_tests/` | Tests for the logic of the pages: the grid, the rules of editing, the editing session and its messages, what counts as a swipe, time and units |
| `package.json` | Only tells Node that the `.js` files are modules. There are no packages to install |

## Run the tests

```
py -m pip install pytest
py -m pytest
```

That runs three kinds of test, and takes about four minutes with all of them:

- **The server's tests.** Always run. They include the check that no address in a page, a
  script or a style starts with a slash. The rules of one editor at a time are tried with a clock
  that the tests move, so nothing waits for the 20-second timer.
- **The pages' logic tests** (`js_tests/`). They need Node.js and are skipped without it.
  They can also be run alone, from this folder: `node --test`. (With nothing after it, Node
  finds the test files by itself. Given the folder's name, some versions of Node fail.)
- **Tests that use the pages in a real browser.** As a desktop: dragging, saving, watching the
  device page redraw, stopping and restarting the server. As a phone, with real touches: the
  home page upright and sideways, and the whole phone editor (taps, swipes, press and hold,
  the panel's screens, loading, saving and leaving). And with several editors open at once:
  two laptops, a phone and a laptop, several phones, taking over, refusing, letting the timer
  run out, and losing the server in the middle. They need Playwright and are skipped without
  it:

  ```
  py -m pip install playwright
  py -m playwright install chromium
  ```

The tests save only into a temporary folder. The browser tests start the server on this
computer only, and nothing reaches the internet.

## The documents' screenshots

The screenshots in `Documentation/` are of the app itself, and a script takes them:

```
py tools/take_screenshots.py
```

It starts the server by itself, on this computer only and with data of its own, opens the
pages in a browser without a window as a laptop and as a phone, plays the situations the
pictures need (a second editor opening, a take-over timer running out, a lost server), and
saves the pictures into the folder of the document they belong to. It needs Playwright, like
the browser tests, and takes about half a minute.

Run it again when something in the pictures changes its look, and look at the new pictures
before keeping them. Every page is told that it is the same moment, 10:30 on 10 March, so a
retaken picture only differs where the app does.

The pictures are grouped in sets, one per document. `py tools/take_screenshots.py --list`
names them, and a name after the command takes only that set. To add a set, write a file in
`tools/screenshots/` that says where its pictures go and plays its scenes, the way
`one_editor_at_a_time.py` does, and add it to the list in `take_screenshots.py`.
