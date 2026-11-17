# web_app

The web app that manages the smart screen, and the server code behind it.

It is being built in steps. So far there is the server: it knows the widgets, stores the
display layout, and checks every layout before saving it. The pages (the editor, the home page
and a stand-in for the device) come next.

## Run it

You need Python 3.9 or newer.

On Windows, in this folder:

```
py -m pip install -r requirements.txt
py run_server.py
```

On Linux or macOS, use `python3` in place of `py`.

The server then answers at http://localhost:8000. Stop it with Ctrl+C.

| Address | What it gives |
|---|---|
| `/api/catalog` | Every widget type, its sizes and its settings; the grid; the backgrounds |
| `/api/layout` | The saved display layout (read with GET, save with PUT) |
| `/api/demo-data` | Example values for the widgets that have no real data source yet |

## What is where

| Folder or file | What it holds |
|---|---|
| `run_server.py` | Starts the server |
| `server/` | The server's code, one file per job |
| `data/widget_catalog.json` | The widgets, the grid and the backgrounds. The single place that defines them |
| `data/default_layout.json` | The layout shown before anything was saved |
| `data/demo_data.json` | **Example data only.** Stands in for the real data sources until they exist |
| `static/backgrounds/` | The six background pictures of the display, 480x320 |
| `tools/make_backgrounds.py` | The script that drew those pictures (needs Pillow and numpy; only run it to change a picture) |
| `tests/` | Tests for the server |

The layout that the user saves is written to `data/saved_layout.json`, which is not kept in the
repository.

## Run the tests

```
py -m pip install pytest
py -m pytest
```

The tests write only into a temporary folder and never use the network.
