# backend/tests/test_export_csv2.py
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def _header_ok(csv_text: str) -> bool:
    want = "itinerary_id,day_id,order,stop_type,stop_id,arrival_min,depart_min,planned_minutes,notes"
    return csv_text.splitlines()[0].strip() == want

def test_export_csv2_has_rows_per_stop_and_ids_only():
    # 1) generate a small itinerary
    gen = client.post("/itinerary/generate", json={"city": "Pittsburgh", "prefs": {"days": 1}})
    assert gen.status_code == 200
    itid = gen.json()["itinerary_id"]

    # 2) ensure meals chosen so lunch/dinner rows may appear
    ap = client.post("/restaurants/auto_pick", json={"itinerary_id": itid})
    assert ap.status_code == 200

    # 3) export csv2
    exp = client.post("/export", json={"itinerary_id": itid, "format": "csv2"})
    assert exp.status_code == 200
    obj = exp.json()
    assert set(obj.keys()) == {"filename", "content_type", "csv_text"}
    csv_text = obj["csv_text"]
    assert _header_ok(csv_text)

    # 4) must have at least the routed POIs as rows (>=1)
    lines = csv_text.strip().splitlines()
    assert len(lines) >= 2  # header + >=1 stop row

    # 5) IDs-only check (no "name" anywhere)
    assert "name" not in csv_text.lower()

def test_export_csv2_kind_and_types():
    gen = client.post("/itinerary/generate", json={"city": "Pittsburgh", "prefs": {"days": 1}})
    assert gen.status_code == 200
    itid = gen.json()["itinerary_id"]

    client.post("/restaurants/auto_pick", json={"itinerary_id": itid})

    exp = client.post("/export", json={"itinerary_id": itid, "format": "csv2"})
    assert exp.status_code == 200
    csv_text = exp.json()["csv_text"]

    # stop_type limited to known kinds (csv2 includes one hotel row)
    allowed = {"poi", "lunch", "dinner", "hotel"}

    # ignore header
    rows = csv_text.splitlines()[1:]
    assert rows, "no data rows in csv2 export"

    seen_hotel = 0
    for row in rows:
        parts = row.split(",")
        # itinerary_id, day_id, order, stop_type, stop_id, ...
        if len(parts) >= 5:
            st = parts[3].strip()
            stop_id = parts[4].strip()
            assert st in allowed
            # basic ID sanity (non-empty)
            assert stop_id != ""

            if st == "hotel":
                seen_hotel += 1

    # csv2 should include at most one hotel row for the itinerary
    assert seen_hotel <= 1

