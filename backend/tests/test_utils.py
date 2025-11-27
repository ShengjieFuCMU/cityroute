from utils.geo import (
    haversine_km,
    km_to_minutes,
    travel_minutes_between,
    detour_minutes,
    centroid_latlon,
)
from utils.timewin import (
    parse_time_hhmm,
    parse_window_str,
    window_overlap_minutes,
    is_open_for_window,
    LUNCH_WINDOW,
    DINNER_WINDOW,
)

def test_geo_haversine_and_time():
    p1 = (40.4414, -80.0089)  # Point State Park
    p2 = (40.4431, -79.9496)  # Carnegie Museum of Art
    d = haversine_km(p1[0], p1[1], p2[0], p2[1])
    assert 4.0 <= d <= 6.0

    mins = km_to_minutes(d, city_speed_kmh=32.0)
    assert 5 <= mins <= 15

    mins2 = travel_minutes_between(p1, p2, city_speed_kmh=32.0)
    assert abs(mins - mins2) < 0.05

    stop = (40.4428, -79.9560)
    det = detour_minutes(p1, p2, stop, city_speed_kmh=32.0)
    assert det >= 0.0

    cent = centroid_latlon([p1, p2])
    assert 40.44 <= cent[0] <= 40.445

def test_time_windows():
    assert parse_time_hhmm("11:30") == 11 * 60 + 30
    assert parse_window_str("11:30-14:00") == (11 * 60 + 30, 14 * 60)

    assert is_open_for_window("11:00-13:00", LUNCH_WINDOW) is True
    assert is_open_for_window("10:00-11:20", LUNCH_WINDOW) is False

    assert is_open_for_window("17:00-18:00", DINNER_WINDOW) is True
    assert is_open_for_window("20:35-21:00", DINNER_WINDOW) is False

    # overlap helper sanity
    assert window_overlap_minutes((600, 700), (650, 800)) == 50

