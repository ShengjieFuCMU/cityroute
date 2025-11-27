from storage.memory import reset_all
from services.planner import generate

def test_determinism_with_filters():
    reset_all()
    pois = [
        {"id":"p1","name":"A","lat":40.4410,"lon":-80.0000,"rating":4.8,"review_count":120,"must_go":True},
        {"id":"p2","name":"B","lat":40.4420,"lon":-80.0010,"rating":4.7,"review_count":110,"must_go":True},
        {"id":"p3","name":"C","lat":40.4460,"lon":-79.9950,"rating":4.6,"review_count":90,"must_go":False},
        {"id":"p4","name":"D","lat":40.4550,"lon":-79.9500,"rating":4.5,"review_count":80,"must_go":False},
        {"id":"p5","name":"E","lat":40.4560,"lon":-79.9510,"rating":4.4,"review_count":70,"must_go":True},
        {"id":"p6","name":"F","lat":40.4710,"lon":-79.9310,"rating":4.3,"review_count":60,"must_go":False},
    ]
    hotels = [{"id":"h1","name":"H","lat":40.445,"lon":-79.998,"rating":4.6,"review_count":400,"price_level":"$$"}]
    restaurants = [{"id":"r1","name":"R","lat":40.4460,"lon":-79.9465,"rating":4.6,"review_count":200,
                    "price_level":"$$","diet_tags":"vegetarian|vegan","open_lunch":"11:30-14:00","open_dinner":"17:30-20:30"}]

    prefs = {"days": 2, "only_must_go": True, "max_pois_total": 4}

    res1 = generate("Pittsburgh", prefs, pois, hotels, restaurants, locks=[], random_state=42)
    res2 = generate("Pittsburgh", prefs, pois, hotels, restaurants, locks=[], random_state=42)

    assert res1["day_ids"] == res2["day_ids"]
    # determinism of visit order across days
    from storage.memory import days
    for did in res1["day_ids"]:
        assert days[did]["visit_ids"] == days[did]["visit_ids"]
    assert res1["hotel_id"] == res2["hotel_id"]

