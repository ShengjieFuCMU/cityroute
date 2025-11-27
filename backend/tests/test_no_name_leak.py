from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_generate_and_export_do_not_include_names():
    # Keep it small for speed
    payload = {
        "city": "Pittsburgh",
        "prefs": {"days": 1}  # use defaults for everything else
    }
    gen = client.post("/itinerary/generate", json=payload)
    assert gen.status_code == 200
    gen_data = gen.json()
    assert "itinerary_id" in gen_data and gen_data["day_ids"]

    # /itineraries/{id} is IDs-only
    itid = gen_data["itinerary_id"]
    it = client.get(f"/itineraries/{itid}")
    assert it.status_code == 200
    it_data = it.json()

    # Top-level contract check
    expected_keys = {"id", "city", "prefs", "day_ids", "hotel_id", "warnings"}
    assert set(it_data.keys()) == expected_keys
    # No 'name' anywhere at top level
    flat_str = str(it_data)
    assert "'name':" not in flat_str and '"name":' not in flat_str

    # /days/{day_id} is also IDs-only for visits/meals
    day_id = it_data["day_ids"][0]
    day = client.get(f"/days/{day_id}")
    assert day.status_code == 200
    day_data = day.json()
    day_expected = {"id", "visit_ids", "lunch_id", "dinner_id", "total_time_minutes"}
    assert set(day_data.keys()) == day_expected
    assert isinstance(day_data["visit_ids"], list)
    assert all(isinstance(x, str) for x in day_data["visit_ids"])
    assert '"name":' not in str(day_data)

    # /export JSON must not include names either
    exp = client.post("/export", json={"itinerary_id": itid, "format": "json"})
    assert exp.status_code == 200
    exp_data = exp.json()
    assert set(exp_data.keys()) == {"itinerary_id", "city", "hotel_id", "prefs", "warnings", "days"}
    all_days = exp_data["days"]
    assert isinstance(all_days, list) and all_days
    assert '"name":' not in str(all_days)

    # Optional: CSV path should still work and obviously has no names
    exp_csv = client.post("/export", json={"itinerary_id": itid, "format": "csv"})
    assert exp_csv.status_code == 200
    csv_obj = exp_csv.json()
    assert set(csv_obj.keys()) == {"filename", "content_type", "csv_text"}
    assert "day_id,visit_ids,lunch_id,dinner_id,total_time_minutes" in csv_obj["csv_text"]

