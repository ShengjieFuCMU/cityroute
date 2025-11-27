from storage.memory import reset_all, days
from services.planner import generate, autopick_meals

def test_generate_smoke_phase1_backend_only():
    reset_all()

    pois = [
        {"id":"p1","name":"A","lat":40.4400,"lon":-80.0000,"rating":4.8,"review_count":100,"must_go":True},
        {"id":"p2","name":"B","lat":40.4410,"lon":-80.0010,"rating":4.7,"review_count":90,"must_go":True},
        {"id":"p3","name":"C","lat":40.4500,"lon":-79.9900,"rating":4.6,"review_count":80,"must_go":False},
    ]
    hotels = [{"id":"h1","name":"H","lat":40.442,"lon":-80.000,"rating":4.6,"review_count":400,"price_level":"$$"}]
    restaurants = [
        {"id":"r1","name":"Near","lat":40.4405,"lon":-80.0005,"rating":4.8,"review_count":300,"price_level":"$$","diet_tags":"vegetarian","open_lunch":"11:30-14:00","open_dinner":"17:30-20:30"},
        {"id":"r2","name":"Far","lat":40.4700,"lon":-79.9300,"rating":4.3,"review_count":50,"price_level":"$","diet_tags":"","open_lunch":"11:30-14:00","open_dinner":"17:30-20:30"},
    ]

    prefs = {
        "days": 1,
        "only_must_go": True,
        "max_pois_total": 5,
        "restaurant_radius_km": 0.5,
        "detour_limit_minutes": 15
    }

    res = generate("Pittsburgh", prefs, pois, hotels, restaurants, locks=[], random_state=42)
    assert "itinerary_id" in res and res["day_ids"]
    itid = res["itinerary_id"]

    m = autopick_meals(itid)
    assert m["days"]
    d0 = m["days"][0]
    assert d0["id"] in res["day_ids"]
    # ensure the day plan exists and has route content
    route = days[d0["id"]]
    assert isinstance(route.get("visit_ids"), list)

