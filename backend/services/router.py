# services/router.py
from __future__ import annotations
from typing import Dict, List, Tuple, Any, Optional
import logging
import os

from dotenv import load_dotenv

from utils.geo import haversine_km, km_to_minutes

# ------------ config & logging ------------
load_dotenv()  # loads from .env if present

# Default city speed (km/h). Can be overridden per-call.
DEFAULT_CITY_SPEED_KMH = float(os.getenv("CITY_SPEED_KMH", "32"))
# Cap on 2-opt iterations (sane default; override per-call)
DEFAULT_ROUTER_MAX_ITERS = int(os.getenv("ROUTER_MAX_ITERS", "200"))

logger = logging.getLogger(__name__)

Coord = Tuple[float, float]


# ------------ helpers ------------
def _distance_km(a: Coord, b: Coord) -> float:
    return haversine_km(a[0], a[1], b[0], b[1])


def _path_length_km(seq: List[Coord]) -> float:
    if len(seq) < 2:
        return 0.0
    total = 0.0
    for i in range(len(seq) - 1):
        total += _distance_km(seq[i], seq[i + 1])
    return total


def _choose_start_index(
    points: List[Coord],
    ids: List[str],
    centroid: Optional[Coord],
    start_id: Optional[str],
) -> int:
    """
    Deterministic start selection:
    - If start_id is provided and present -> use it.
    - Else if centroid given -> use the point nearest to the centroid.
    - Else use 'leftmost' (min lon, then min lat) as a stable tie-break.
    """
    if start_id and start_id in ids:
        return ids.index(start_id)

    if centroid is not None:
        best = 0
        bestd = float("inf")
        for i, p in enumerate(points):
            d = _distance_km(centroid, p)
            if d < bestd:
                bestd = d
                best = i
        return best

    # fallback: deterministic leftmost
    best = 0
    best_key = (points[0][1], points[0][0])  # (lon, lat)
    for i, (lat, lon) in enumerate(points):
        key = (lon, lat)
        if key < best_key:
            best_key = key
            best = i
    return best


def _nearest_neighbor(points: List[Coord], ids: List[str], start_idx: int) -> Tuple[List[Coord], List[str]]:
    n = len(points)
    if n <= 1:
        return points[:], ids[:]

    unvisited = list(range(n))
    order_idx: List[int] = []
    # start
    order_idx.append(start_idx)
    unvisited.remove(start_idx)

    current = start_idx
    while unvisited:
        # pick nearest unvisited to current
        best_j = unvisited[0]
        best_d = _distance_km(points[current], points[best_j])
        for j in unvisited[1:]:
            d = _distance_km(points[current], points[j])
            if d < best_d:
                best_d = d
                best_j = j
        order_idx.append(best_j)
        unvisited.remove(best_j)
        current = best_j

    route_pts = [points[i] for i in order_idx]
    route_ids = [ids[i] for i in order_idx]
    return route_pts, route_ids


def _two_opt(
    route_pts: List[Coord],
    route_ids: List[str],
    max_iters: int,
) -> Tuple[List[Coord], List[str]]:
    """
    Standard 2-opt for open path (no return to start). Keeps endpoints fixed.
    """
    if len(route_pts) < 4:
        return route_pts, route_ids

    improved = True
    iters = 0
    while improved and iters < max_iters:
        improved = False
        iters += 1
        # endpoints i=0 and j=len-1 are fixed
        for i in range(1, len(route_pts) - 2):
            for j in range(i + 1, len(route_pts) - 1):
                # edges: (i-1 -> i) and (j -> j+1) replaced by (i-1 -> j) and (i -> j+1)
                a, b = route_pts[i - 1], route_pts[i]
                c, d = route_pts[j], route_pts[j + 1]
                old = _distance_km(a, b) + _distance_km(c, d)
                new = _distance_km(a, c) + _distance_km(b, d)
                if new + 1e-9 < old:
                    # reverse the segment [i..j]
                    route_pts[i : j + 1] = reversed(route_pts[i : j + 1])
                    route_ids[i : j + 1] = reversed(route_ids[i : j + 1])
                    improved = True
        # loop again if any improvement
    return route_pts, route_ids


# ------------ public API ------------
def route_day(
    pois: List[Dict[str, Any]],
    *,
    centroid: Optional[Coord] = None,
    start_id: Optional[str] = None,
    city_speed_kmh: Optional[float] = None,
    max_iters: Optional[int] = None,
) -> Tuple[List[str], float, float]:
    """
    Build a day's route:
      - NN starting near centroid (or at start_id if provided)
      - 2-opt improvement

    Args:
        pois: list of POI dicts with keys: id, lat, lon
        centroid: (lat, lon) used to choose a stable, deterministic start
        start_id: POI id to force as the start (if present)
        city_speed_kmh: override speed; defaults to env CITY_SPEED_KMH (32)
        max_iters: override 2-opt iteration cap; defaults from env ROUTER_MAX_ITERS (200)

    Returns:
        (ordered_visit_ids, total_time_minutes, total_distance_km)
    """
    if not pois:
        return [], 0.0, 0.0

    city_speed_kmh = float(city_speed_kmh or DEFAULT_CITY_SPEED_KMH)
    max_iters = int(max_iters or DEFAULT_ROUTER_MAX_ITERS)

    ids = [p["id"] for p in pois]
    pts = [(float(p["lat"]), float(p["lon"])) for p in pois]

    sidx = _choose_start_index(pts, ids, centroid, start_id)
    nn_pts, nn_ids = _nearest_neighbor(pts, ids, sidx)
    opt_pts, opt_ids = _two_opt(nn_pts, nn_ids, max_iters=max_iters)

    # compute distance/time
    dist_km = _path_length_km(opt_pts)
    time_min = km_to_minutes(dist_km, city_speed_kmh=city_speed_kmh)

    logger.debug(
        "route_day: n=%d start=%s dist=%.3fkm time=%.1fmin speed=%.1f iters=%d",
        len(pois), opt_ids[0] if opt_ids else "NA", dist_km, time_min, city_speed_kmh, max_iters
    )

    return opt_ids, float(time_min), float(dist_km)

