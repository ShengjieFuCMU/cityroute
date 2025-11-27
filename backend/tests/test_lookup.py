from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_lookup_ok_poi():
    # Uses seeded IDs from data/pois.csv
    resp = client.get("/lookup/poi", params={"ids": "poi1,poi3"})
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data and isinstance(data["items"], list)
    assert [it["id"] for it in data["items"]] == ["poi1", "poi3"]
    # Name may be None if CSV row lacks name, but key must exist
    assert "name" in data["items"][0]


def test_lookup_ok_hotel_and_restaurant():
    # Hotels
    resp_h = client.get("/lookup/hotel", params={"ids": "h1,h3"})
    assert resp_h.status_code == 200
    items_h = resp_h.json()["items"]
    assert [it["id"] for it in items_h] == ["h1", "h3"]
    assert "name" in items_h[0]

    # Restaurants
    resp_r = client.get("/lookup/restaurant", params={"ids": "r1,r20"})
    assert resp_r.status_code == 200
    items_r = resp_r.json()["items"]
    assert [it["id"] for it in items_r] == ["r1", "r20"]
    assert "name" in items_r[0]


def test_lookup_kind_guard():
    resp = client.get("/lookup/not_a_kind", params={"ids": "x"})
    assert resp.status_code == 400
    assert "poi|hotel|restaurant" in resp.json()["detail"]


def test_lookup_empty_ids_guard():
    # ids present but empty string -> 400
    resp = client.get("/lookup/poi", params={"ids": ""})
    assert resp.status_code == 400
    assert "non-empty" in resp.json()["detail"].lower()


def test_lookup_handles_unknown_ids():
    resp = client.get("/lookup/poi", params={"ids": "unknown123"})
    assert resp.status_code == 200
    assert resp.json()["items"] == [{"id": "unknown123", "name": None}]

