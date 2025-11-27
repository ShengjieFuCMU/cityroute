# backend/utils/_scratch_test.py
from utils.geo import haversine_km, km_to_minutes, travel_minutes_between, detour_minutes, centroid_latlon
from utils.timewin import parse_time_hhmm, parse_window_str, window_overlap_minutes, is_open_for_window, LUNCH_WINDOW, DINNER_WINDOW

def test_geo():
    # Pittsburgh approximate: Point State Park and Carnegie Museum of Art
    p1 = (40.4414, -80.0089)  # Point State Park
    p2 = (40.4431, -79.9496)  # Carnegie Museum of Art
    d = haversine_km(p1[0], p1[1], p2[0], p2[1])
    assert 4.0 <= d <= 6.0, f"distance too off: {d:.2f} km"

    mins = km_to_minutes(d, city_speed_kmh=32.0)
    assert 5 <= mins <= 15, f"unexpected minutes: {mins:.1f}"

    mins2 = travel_minutes_between(p1, p2, city_speed_kmh=32.0)
    assert abs(mins - mins2) < 0.01

    # detour: insert a stop somewhat “between” them (roughly Oakland)
    stop = (40.4428, -79.9560)
    det = detour_minutes(p1, p2, stop, city_speed_kmh=32.0)
    assert det >= 0.0, f"detour must be non-negative: {det}"
    # Not asserting a tight range because this is a rough estimate.

    cent = centroid_latlon([p1, p2])
    assert 40.44 <= cent[0] <= 40.445, "centroid lat out of range"

def test_timewin():
    assert parse_time_hhmm("11:30") == 11*60 + 30
    assert parse_time_hhmm("8:05") == 8*60 + 5

    w = parse_window_str("11:30–14:00")
    assert w == (11*60+30, 14*60)

    # overlap with lunch window
    assert is_open_for_window("11:00-13:00", LUNCH_WINDOW) is True
    assert is_open_for_window("10:00-11:20", LUNCH_WINDOW) is False

    # dinner window tests
    assert is_open_for_window("17:00-18:00", DINNER_WINDOW) is True
    assert is_open_for_window("20:35-21:00", DINNER_WINDOW) is False

    # non-increasing window should fail parsing
    try:
        parse_window_str("14:00-11:30")
        assert False, "expected ValueError for non-increasing window"
    except ValueError:
        pass

if __name__ == "__main__":
    test_geo()
    test_timewin()
    print("All good ✅")

