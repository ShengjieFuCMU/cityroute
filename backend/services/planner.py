# services/planner.py
from __future__ import annotations
from typing import List, Dict, Any, Tuple, Optional
import logging
import os
import time

from dotenv import load_dotenv

from services.clusterer import cluster_pois_kmeans
from services.router import route_day
from services.hotel_ranker import rank_hotels
from services.restaurants import autopick_for_day
from services.poi_filter import apply_must_go, cap_top_k
from storage.memory import itineraries, days, next_itinerary_id, next_day_id
from utils.geo import centroid_latlon

# ------------ config & logging ------------
load_dotenv()

# Daily time budget in minutes (default 7 hours).
DAILY_TIME_BUDGET_MIN = int(os.getenv("DAILY_TIME_BUDGET_MIN", str(7 * 60)))
# Default detour limit for meals.
DEFAULT_DETOUR_MIN = float(os.getenv("DEFAULT_DETOUR_MIN", "15"))
# City travel speed (passed to router/meals if not overridden).
DEFAULT_CITY_SPEED_KMH = float(os.getenv("CITY_SPEED_KMH", "32"))
# Optional router 2-opt cap
DEFAULT_ROUTER_MAX_ITERS = int(os.getenv("ROUTER_MAX_ITERS", "200"))
# Optional clusterer random state for determinism
DEFAULT_CLUSTER_RANDOM_STATE = int(os.getenv("CLUSTER_RANDOM_STATE", "42"))

logger = logging.getLogger(__name__)


def _build_poi_index(pois: List[Dict[str, Any]]) -> Dict[str, Tuple[float, float]]:
    return {p["id"]: (float(p["lat"]), float(p["lon"])) for p in pois}


def generate(
    city: str,
    prefs: Dict[str, Any],
    pois: List[Dict[str, Any]],
    hotels: List[Dict[str, Any]],
    restaurants: List[Dict[str, Any]],
    locks: Optional[List[Dict[str, Any]]] = None,
    *,
    random_state: Optional[int] = None,
    router_max_iters: Optional[int] = None,
    city_speed_kmh: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Pipeline: (Phase 1 filters) → cluster → per-day route → centroids → hotel rank → store IDs-only itinerary.

    Optional kwargs:
      random_state: forwarded to clusterer for deterministic KMeans.
      router_max_iters: forwarded to router 2-opt.
      city_speed_kmh: speed used for time estimates (overrides env).
    """
    t0 = time.perf_counter()
    locks = locks or []
    warnings: List[str] = []

    K = int(prefs.get("days", 3))
    city_speed_kmh = float(city_speed_kmh or prefs.get("city_speed_kmh") or DEFAULT_CITY_SPEED_KMH)
    router_max_iters = int(router_max_iters or DEFAULT_ROUTER_MAX_ITERS)
    rs = int(random_state if random_state is not None else DEFAULT_CLUSTER_RANDOM_STATE)

    # ----- Phase 1: POI selection controls -----
    only_must_go = bool(prefs.get("only_must_go", False))
    max_pois_total = int(prefs.get("max_pois_total", 40))

    # Phase 3: validation — cap must be ≥ number of days
    if max_pois_total < K:
        # app.py will convert this ValueError into a 400 with the same message
        raise ValueError("max_pois_total must be ≥ days")

    filtered = apply_must_go(pois, only_must_go)
    if only_must_go and not filtered:
        # explicit, user-actionable message
        raise ValueError("No POIs are marked must_go. Relax only_must_go=False or update POI flags.")

    trimmed, did_trim = cap_top_k(filtered, max_pois_total)
    if did_trim:
        warnings.append(f"POIs were trimmed to max_pois_total={max_pois_total}.")
    pois = trimmed

    # Optional: lock hotel id if provided
    locked_hotel_id: Optional[str] = None
    for L in locks:
        if L.get("type") == "hotel":
            locked_hotel_id = L.get("id")

    # 1) Cluster
    t1 = time.perf_counter()
    cl = cluster_pois_kmeans(pois, K, random_state=rs)
    clusters = cl.get("clusters", [])
    warnings.extend(cl.get("warnings", []))

    # Phase 3: warn if fewer clusters than requested days (after filtering/capping)
    if len(clusters) < K:
        warnings.append("Fewer clusters than days after filtering")

    t2 = time.perf_counter()
    logger.info(
        "planner.generate: cluster K=%d -> %d clusters in %.3fs (warnings=%d)",
        K, len(clusters), (t2 - t1), len(warnings)
    )

    # 2) Per-day routing & DayPlan creation
    poi_by_id = {p["id"]: p for p in pois}
    day_ids: List[str] = []
    day_centroids: List[Tuple[float, float]] = []

    route_warns = 0
    for cluster in clusters:
        day_id = cluster.get("day_id") or next_day_id()
        poi_ids = cluster.get("poi_ids", [])
        day_pois = [poi_by_id[pid] for pid in poi_ids if pid in poi_by_id]

        c = cluster.get("centroid")
        r_start = time.perf_counter()
        ordered_ids, total_minutes, _dist_km = route_day(
            day_pois,
            centroid=c,
            city_speed_kmh=city_speed_kmh,
            max_iters=router_max_iters,
        )
        r_end = time.perf_counter()

        if total_minutes > DAILY_TIME_BUDGET_MIN:
            warnings.append(
                f"{day_id} exceeds daily time budget ({total_minutes:.0f}m > {DAILY_TIME_BUDGET_MIN}m); "
                f"consider adding a day or reducing POIs."
            )
            route_warns += 1

        coords = [(poi_by_id[i]["lat"], poi_by_id[i]["lon"]) for i in ordered_ids]
        day_center = centroid_latlon(coords) if coords else (c or (0.0, 0.0))
        day_centroids.append(day_center)

        days[day_id] = {
            "id": day_id,
            "visit_ids": ordered_ids,
            "lunch_id": None,
            "dinner_id": None,
            "total_time_minutes": round(float(total_minutes), 1),
        }
        day_ids.append(day_id)

        logger.info(
            "planner.generate: routed %s with %d POIs in %.3fs (time=%.1f min, speed=%.1f km/h)",
            day_id, len(day_pois), (r_end - r_start), total_minutes, city_speed_kmh
        )

    # 3) Hotel rank (respect lock if given)
    t3 = time.perf_counter()
    if locked_hotel_id:
        hotel_id = locked_hotel_id
    else:
        ordered = rank_hotels(hotels, day_centroids)
        hotel_id = ordered[0] if ordered else None
        if not hotel_id:
            warnings.append("No hotels available to rank.")
    t4 = time.perf_counter()
    logger.info("planner.generate: hotel rank in %.3fs", (t4 - t3))

    # 4) Save itinerary with cached inputs for later autopick/regenerate
    itin_id = next_itinerary_id()
    itineraries[itin_id] = {
        "id": itin_id,
        "city": city,
        "prefs": prefs,
        "day_ids": day_ids,
        "hotel_id": hotel_id,
        "warnings": warnings,
        # cache inputs
        "_pois": pois,
        "_hotels": hotels,
        "_restaurants": restaurants,
        "_poi_index": _build_poi_index(pois),
        "_locks": locks,
    }

    t5 = time.perf_counter()
    logger.info(
        "planner.generate: done itin=%s in %.3fs (cluster=%.3fs, route=%s, hotel=%.3fs, route_warnings=%d, total_warnings=%d)",
        itin_id,
        (t5 - t0),
        (t2 - t1),
        "mixed",  # per-day timings logged above
        (t4 - t3),
        route_warns,
        len(warnings),
    )

    return {
        "itinerary_id": itin_id,
        "day_ids": day_ids,
        "hotel_id": hotel_id,
        "warnings": warnings,
    }


def autopick_meals(
    itinerary_id: str,
    day_ids: Optional[List[str]] = None,
    *,
    detour_limit_min: Optional[float] = None,
    city_speed_kmh: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Fill lunch/dinner for selected days (or all days if None) with no-repeat across the whole itinerary.
    """
    it = itineraries.get(itinerary_id)
    if not it:
        return {"days": [], "warnings": [f"Itinerary {itinerary_id} not found."]}

    poi_index = it["_poi_index"]
    restaurants = it["_restaurants"]
    prefs = it["prefs"]
    all_day_ids = day_ids or it["day_ids"]

    # defaults
    detour_limit_min = float(detour_limit_min or prefs.get("detour_limit_minutes") or DEFAULT_DETOUR_MIN)
    city_speed_kmh = float(city_speed_kmh or prefs.get("city_speed_kmh") or DEFAULT_CITY_SPEED_KMH)

    used_ids = set()
    for did in it["day_ids"]:
        d = days.get(did)
        if d:
            if d.get("lunch_id"):
                used_ids.add(d["lunch_id"])
            if d.get("dinner_id"):
                used_ids.add(d["dinner_id"])

    out = []
    for did in all_day_ids:
        d = days.get(did)
        if not d:
            continue
        route_pts = [(poi_index[pid][0], poi_index[pid][1]) for pid in d["visit_ids"] if pid in poi_index]

        lunch_id, dinner_id, notes = autopick_for_day(
            route_pts,
            restaurants,
            prefs=prefs,
            detour_limit_min=detour_limit_min,
            city_speed_kmh=city_speed_kmh,
            used_ids=used_ids,  # enforce no-repeat across itinerary
        )

        if lunch_id:
            d["lunch_id"] = lunch_id
            used_ids.add(lunch_id)
        if dinner_id:
            d["dinner_id"] = dinner_id
            used_ids.add(dinner_id)

        out.append({"id": did, "lunch_id": d.get("lunch_id"), "dinner_id": d.get("dinner_id"), "notes": notes})

    return {"days": out}


def regenerate_with_locks(
    itinerary_id: str,
    locks: Optional[List[Dict[str, Any]]] = None,
    *,
    random_state: Optional[int] = None,
    router_max_iters: Optional[int] = None,
    city_speed_kmh: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Re-run generate with the cached inputs, applying new locks.
    """
    it = itineraries.get(itinerary_id)
    if not it:
        return {"warnings": [f"Itinerary {itinerary_id} not found."]}

    city = it["city"]
    prefs = it["prefs"]
    pois = it["_pois"]
    hotels = it["_hotels"]
    restaurants = it["_restaurants"]

    return generate(
        city,
        prefs,
        pois,
        hotels,
        restaurants,
        locks=locks or [],
        random_state=random_state,
        router_max_iters=router_max_iters,
        city_speed_kmh=city_speed_kmh,
    )

