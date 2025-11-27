from services.router import route_day

def test_route_day_basic():
    pois = [
        {"id":"p1","name":"A","lat":40.4410,"lon":-80.0000},
        {"id":"p2","name":"B","lat":40.4420,"lon":-80.0020},
        {"id":"p3","name":"C","lat":40.4460,"lon":-79.9950},
        {"id":"p4","name":"D","lat":40.4445,"lon":-79.9975},
        {"id":"p5","name":"E","lat":40.4470,"lon":-79.9920},
    ]
    centroid = (40.444, -79.998)

    # updated kwarg name: max_iters (instead of two_opt_max_iters)
    ids, minutes, dist_km = route_day(pois, centroid=centroid, max_iters=100)

    assert set(ids) == {p["id"] for p in pois}
    assert 0.0 < dist_km < 20.0
    assert 0.0 < minutes < 60.0

def test_route_day_start_lock():
    pois = [
        {"id":"p1","name":"A","lat":40.4410,"lon":-80.0000},
        {"id":"p2","name":"B","lat":40.4420,"lon":-80.0020},
        {"id":"p3","name":"C","lat":40.4460,"lon":-79.9950},
        {"id":"p4","name":"D","lat":40.4445,"lon":-79.9975},
    ]
    ids, _, _ = route_day(pois, start_id="p3")
    assert ids[0] == "p3"

