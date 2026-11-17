"""The server's addresses, called the way a browser would call them."""
import json

from server.app import LARGEST_REQUEST_BYTES, create_app


def test_read_layout_returns_the_default_before_any_save(client, default_layout):
    response = client.get("/api/layout")
    assert response.status_code == 200
    assert response.get_json() == {"revision": 0, "saved_at": None, "layout": default_layout}


def test_saving_a_good_layout_returns_its_revision(client, one_clock_layout):
    response = client.put("/api/layout", json=one_clock_layout)
    assert response.status_code == 200
    answer = response.get_json()
    assert answer["revision"] == 1
    assert answer["saved_at"]


def test_a_saved_layout_is_what_read_layout_returns_next(client, one_clock_layout):
    client.put("/api/layout", json=one_clock_layout)
    answer = client.get("/api/layout").get_json()
    assert answer["layout"] == one_clock_layout
    assert answer["revision"] == 1


def test_a_saved_layout_is_still_there_after_a_restart(client, config, one_clock_layout):
    client.put("/api/layout", json=one_clock_layout)
    restarted_client = create_app(config).test_client()
    assert restarted_client.get("/api/layout").get_json()["layout"] == one_clock_layout


def test_a_layout_that_breaks_a_rule_is_refused_with_the_reason(client, one_clock_layout):
    one_clock_layout["screens"][0]["widgets"][0]["col"] = 5
    response = client.put("/api/layout", json=one_clock_layout)
    assert response.status_code == 400
    errors = response.get_json()["errors"]
    assert len(errors) == 1
    assert "does not fit inside the grid" in errors[0]


def test_a_refused_layout_changes_nothing(client, config, default_layout, one_clock_layout):
    one_clock_layout["version"] = 99
    client.put("/api/layout", json=one_clock_layout)
    assert client.get("/api/layout").get_json() == {"revision": 0, "saved_at": None, "layout": default_layout}
    assert not config.saved_layout_path.exists()


def test_a_request_that_is_not_json_is_refused(client):
    response = client.put("/api/layout", data="not json", content_type="application/json")
    assert response.status_code == 400
    assert response.get_json()["errors"]


def test_a_request_without_a_json_content_type_is_refused(client, one_clock_layout):
    response = client.put("/api/layout", data=json.dumps(one_clock_layout), content_type="text/plain")
    assert response.status_code == 400


def test_a_request_far_larger_than_a_layout_is_refused(client):
    oversized = json.dumps({"padding": "x" * (LARGEST_REQUEST_BYTES + 1)})
    response = client.put("/api/layout", data=oversized, content_type="application/json")
    assert response.status_code in (400, 413)
    assert client.get("/api/layout").get_json()["revision"] == 0


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
