from services.planner import generate, autopick_meals
from storage.memory import reset_all, days

def test_restaurant_radius_prefilter_and_fallback():
    reset_all()
    # Make a tiny day near (40.44,-80.00)
    pois = [
        {"id":"p1","name":"A","lat":40.4400,"lon":-80.0000,"rating":4.8,"review_count":100,"must_go":True},
        {"id":"p2","name":"B","lat":40.4410,"lon":-80.0010,"rating":4.7,"review_count":90,"must_go":True},
    ]
    hotels = [{"id":"h1","name":"H","lat":40.442,"lon":-80.000,"rating":4.6,"review_count":400,"price_level":"$$"}]
    restaurants = [
        {"id":"near","name":"Near","lat":40.4405,"lon":-80.0005,"rating":4.8,"review_count":300,"price_level":"$$","diet_tags":"vegetarian","open_lunch":"11:30-14:00","open_dinner":"17:30-20:30"},
        {"id":"far","name":"Far","lat":40.4700,"lon":-79.9300,"rating":4.9,"review_count":1000,"price_level":"$$$","diet_tags":"vegetarian","open_lunch":"11:30-14:00","open_dinner":"17:30-20:30"},
    ]

    # radius tight enough to include "near" but exclude "far"
    prefs = {"days": 1, "restaurant_radius_km": 0.5, "detour_limit_minutes": 15}

    res = generate("Pittsburgh", prefs, pois, hotels, restaurants, locks=[], random_state=42)
    itid = res["itinerary_id"]
    meals = autopick_meals(itid)

    day = meals["days"][0]
    # Expect that within-radius restaurant gets picked for at least one meal
    assert day["lunch_id"] == "near" or day["dinner_id"] == "near"

    # Now force a tiny radius so neither qualifies, ensure fallback note appears
    reset_all()
    res2 = generate("Pittsburgh", {"days":1, "restaurant_radius_km": 0.01}, pois, hotels, restaurants, locks=[], random_state=42)
    m2 = autopick_meals(res2["itinerary_id"])
    notes_text = " ".join(" ".join(d["notes"]) for d in m2["days"])
    assert "falling back to global pool" in notes_text.lower()

