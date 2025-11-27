from services.planner import generate
from storage.memory import reset_all, days

def test_max_pois_total_cap_respected():
    reset_all()
    # 50 synthetic POIs, all must_go True to stress the cap
    pois = []
    for i in range(50):
        pois.append({
            "id": f"p{i:02d}",
            "name": f"P{i:02d}",
            "lat": 40.40 + 0.001*i,
            "lon": -80.00 + 0.001*i,
            "rating": 4.0 + (i % 10) * 0.01,
            "review_count": 100 + i,
            "must_go": True
        })
    hotels = [{"id":"h1","name":"H","lat":40.44,"lon":-79.99,"rating":4.6,"review_count":400,"price_level":"$$"}]
    restaurants = []

    prefs = {"days": 3, "only_must_go": True, "max_pois_total": 40}
    res = generate("Pittsburgh", prefs, pois, hotels, restaurants, locks=[], random_state=42)

    total_visits = sum(len(days[did]["visit_ids"]) for did in res["day_ids"])
    # We can route fewer than the cap if K * avg cluster splits result in <40, but must never exceed the cap
    assert total_visits <= 40

