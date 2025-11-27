# backend/utils/geo.py
# Utilities for geographic distance and simple travel-time estimates.

from math import radians, sin, cos, asin, sqrt
from typing import Iterable, Tuple, List, Optional

EARTH_RADIUS_KM = 6371.0088

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Great-circle distance between two points on Earth in kilometers.
    Accurate enough for city-scale routing/estimates.
    """
    lat1, lon1, lat2, lon2 = map(radians, (lat1, lon1, lat2, lon2))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return EARTH_RADIUS_KM * c

def path_length_km(points: List[Tuple[float, float]]) -> float:
    """
    Total distance along a path: sum of consecutive haversine segments.
    points: [(lat, lon), (lat, lon), ...]
    """
    if len(points) < 2:
        return 0.0
    dist = 0.0
    for i in range(len(points) - 1):
        lat1, lon1 = points[i]
        lat2, lon2 = points[i+1]
        dist += haversine_km(lat1, lon1, lat2, lon2)
    return dist

def centroid_latlon(points: Iterable[Tuple[float, float]]) -> Tuple[float, float]:
    """
    Simple arithmetic centroid of lat/lon points.
    Good enough for scoring hotels vs day centers.
    """
    pts = list(points)
    if not pts:
        raise ValueError("centroid_latlon: empty point list")
    lat_sum = sum(p[0] for p in pts)
    lon_sum = sum(p[1] for p in pts)
    return (lat_sum / len(pts), lon_sum / len(pts))

def km_to_minutes(distance_km: float,
                  city_speed_kmh: float = 32.0,
                  min_speed_kmh: float = 10.0,
                  max_speed_kmh: float = 50.0) -> float:
    """
    Convert kilometers to minutes using a bounded city driving speed.
    We clamp speed to [min_speed_kmh, max_speed_kmh].
    """
    spd = max(min_speed_kmh, min(city_speed_kmh, max_speed_kmh))
    return (distance_km / spd) * 60.0

def travel_minutes_between(a: Tuple[float, float],
                           b: Tuple[float, float],
                           **speed_kwargs) -> float:
    """
    Quick travel time estimate between two points (minutes), using haversine and km_to_minutes.
    """
    d_km = haversine_km(a[0], a[1], b[0], b[1])
    return km_to_minutes(d_km, **speed_kwargs)

def detour_minutes(prev_pt: Tuple[float, float],
                   next_pt: Tuple[float, float],
                   stop_pt: Tuple[float, float],
                   **speed_kwargs) -> float:
    """
    Approximate extra time to add a STOP between PREV and NEXT.
    detour = time(prev->stop) + time(stop->next) - time(prev->next)
    Used to bound meal detours (e.g., <= 15 minutes).
    """
    base = travel_minutes_between(prev_pt, next_pt, **speed_kwargs)
    with_stop = (travel_minutes_between(prev_pt, stop_pt, **speed_kwargs) +
                 travel_minutes_between(stop_pt, next_pt, **speed_kwargs))
    return max(0.0, with_stop - base)

