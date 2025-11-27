from services.planner import generate
from storage.memory import reset_all

def test_only_must_go_subset():
    reset_all()
    pois = [
        {"id":"a","name":"A","lat":40.44,"lon":-80.00,"rating":4.8,"review_count":100,"must_go":True},
        {"id":"b","name":"B","lat":40.45,"lon":-79.99,"rating":4.2,"review_count":50,"must_go":False},
        {"id":"c","name":"C","lat":40.46,"lon":-79.98,"rating":4.5,"review_count":80,"must_go":True},
        {"id":"d","name":"D","lat":40.47,"lon":-79.97,"rating":4.1,"review_count":20,"must_go":False},
    ]
    hotels = [{"id":"h1","name":"H","lat":40.445,"lon":-79.998,"rating":4.6,"review_count":400,"price_level":"$$"}]
    restaurants = []

    prefs = {"days": 2, "only_must_go": True, "max_pois_total": 40}
    res = generate("Pittsburgh", prefs, pois, hotels, restaurants, locks=[], random_state=42)

    # collect all POIs that appear in visits
    from storage.memory import days
    visit_ids = []
    for did in res["day_ids"]:
        visit_ids.extend(days[did]["visit_ids"])
    # all must be from the must_go set
    assert set(visit_ids).issubset({"a", "c"})
    assert len(visit_ids) <= 2  # we only had 2 must_go

