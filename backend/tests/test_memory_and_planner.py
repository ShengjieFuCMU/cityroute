from storage.memory import reset_all, snapshot_counts
from services.planner import generate, autopick_meals

def test_memory_reset_and_counts():
    reset_all()
    assert snapshot_counts() == (0, 0)

def test_planner_generate_and_autopick_small():
    reset_all()
    pois = [
        {"id":"p1","name":"A","lat":40.4410,"lon":-80.0000,"rating":4.5,"review_count":100,"must_go":True},
        {"id":"p2","name":"B","lat":40.4420,"lon":-80.0020,"rating":4.2,"review_count":80,"must_go":False},
        {"id":"p3","name":"C","lat":40.4460,"lon":-79.9950,"rating":4.1,"review_count":50,"must_go":False},
    ]
    hotels = [
        {"id":"h1","name":"Hotel A","lat":40.445,"lon":-79.998,"rating":4.6,"review_count":400,"price_level":"$$"},
        {"id":"h2","name":"Hotel B","lat":40.468,"lon":-79.935,"rating":4.1,"review_count":120,"price_level":"$$"},
    ]
    restaurants = [
        {"id":"r1","name":"Veggie","lat":40.4460,"lon":-79.9465,"rating":4.6,"review_count":200,"price_level":"$$","diet_tags":"vegetarian|vegan","open_lunch":"11:30-14:00","open_dinner":"17:30-20:30"},
        {"id":"r2","name":"Any","lat":40.4518,"lon":-79.9425,"rating":4.5,"review_count":120,"price_level":"$","diet_tags":"","open_lunch":"11:30-14:00","open_dinner":"17:30-20:30"},
    ]
    prefs = {"days": 2, "travel_mode": "drive", "detour_limit_minutes": 15}

    res = generate("Pittsburgh", prefs, pois, hotels, restaurants, locks=[], random_state=42, router_max_iters=100, city_speed_kmh=32.0)
    assert "itinerary_id" in res and len(res["day_ids"]) == 2

    meals = autopick_meals(res["itinerary_id"])
    assert len(meals["days"]) == 2

