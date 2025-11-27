# backend/tests/test_validation.py
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_max_pois_lt_days_400():
    payload = {
        "city": "Pittsburgh",
        "prefs": {"days": 3, "max_pois_total": 2, "only_must_go": False}
    }
    r = client.post("/itinerary/generate", json=payload)
    assert r.status_code == 400
    assert "max_pois_total must be ≥ days" in r.json()["detail"]

# backend/tests/test_validation.py
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_only_must_go_zero_400():
    # Provide custom POIs with no must_go, so only_must_go=True must fail deterministically
    payload = {
        "city": "Pittsburgh",
        "prefs": {"days": 1, "only_must_go": True},
        "pois": [
            {"id": "p1", "name": "A", "lat": 40.44,  "lon": -80.00, "rating": 4.5, "review_count": 100, "must_go": False},
            {"id": "p2", "name": "B", "lat": 40.441, "lon": -80.001, "rating": 4.2, "review_count": 80,  "must_go": False},
        ],
        # Minimal hotel/restaurant seeds so /itinerary/generate can execute until the must_go check
        "hotels": [
            {"id": "h1", "name": "H", "lat": 40.445, "lon": -79.998, "rating": 4.6, "review_count": 400, "price_level": "$$"}
        ],
        "restaurants": []
    }
    r = client.post("/itinerary/generate", json=payload)
    assert r.status_code == 400
    assert "No POIs are marked must_go" in r.json()["detail"]

def test_cluster_less_than_k_warns():
    # Force fewer POIs than days to trigger the warning
    # Pass tiny inlined POI list to avoid relying on seeds.
    small_pois = [
        {"id":"p1","name":"A","lat":40.44,"lon":-80.00,"rating":4.8,"review_count":10,"must_go":True},
        {"id":"p2","name":"B","lat":40.441,"lon":-80.001,"rating":4.7,"review_count":9,"must_go":True},
    ]
    hotels = [{"id":"h1","name":"H","lat":40.445,"lon":-79.998,"rating":4.6,"review_count":400,"price_level":"$$"}]
    restaurants = []

    payload = {
        "city": "Pittsburgh",
        "prefs": {"days": 3, "max_pois_total": 40},
        "pois": small_pois,
        "hotels": hotels,
        "restaurants": restaurants
    }
    r = client.post("/itinerary/generate", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "warnings" in data
    joined = " ".join(data["warnings"]).lower()
    assert "fewer clusters than days after filtering" in joined

