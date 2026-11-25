"""The server's addresses, called the way a browser would call them."""
from live_channel import save_as_an_editor
from server.app import create_app


def test_read_layout_returns_the_default_before_any_save(client, default_layout):
    response = client.get("/api/layout")
    assert response.status_code == 200
    assert response.get_json() == {"revision": 0, "saved_at": None, "layout": default_layout}


def test_a_saved_layout_is_what_read_layout_returns_next(config, one_clock_layout):
    app = create_app(config)
    save_as_an_editor(app, one_clock_layout)
    answer = app.test_client().get("/api/layout").get_json()
    assert answer["layout"] == one_clock_layout
    assert answer["revision"] == 1
    assert answer["saved_at"]


def test_a_saved_layout_is_still_there_after_a_restart(config, one_clock_layout):
    save_as_an_editor(create_app(config), one_clock_layout)
    restarted_client = create_app(config).test_client()
    assert restarted_client.get("/api/layout").get_json()["layout"] == one_clock_layout


def test_a_layout_cannot_be_saved_from_outside_the_editing_rules(client, config, default_layout, one_clock_layout):
    # The address that used to save any layout sent to it no longer does.
    response = client.put("/api/layout", json=one_clock_layout)
    assert response.status_code == 405
    assert client.get("/api/layout").get_json() == {"revision": 0, "saved_at": None, "layout": default_layout}
    assert not config.saved_layout_path.exists()


def test_read_catalog_returns_the_grid_the_widgets_and_the_backgrounds(client):
    catalog = client.get("/api/catalog").get_json()
    assert catalog["grid"] == {"columns": 6, "rows": 4, "cell_pixels": 80}
    assert {entry["type"] for entry in catalog["widgets"]} == {
        "clock", "date", "weather", "stock", "exchange_rate", "room_climate", "reminders",
    }
    assert len(catalog["backgrounds"]) == 6


def test_demo_data_says_that_it_is_example_data(client):
    demo_data = client.get("/api/demo-data").get_json()
    assert "EXAMPLE DATA" in demo_data["about"]
    assert demo_data["reminders"]
