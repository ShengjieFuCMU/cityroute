# backend/services/hotel_ranker.py
from __future__ import annotations
from typing import List, Dict, Any, Tuple, Optional
import math

from utils.geo import haversine_km

Coord = Tuple[float, float]

def _avg_distance_to_points(lat: float, lon: float, points: List[Coord]) -> float:
    if not points:
        return 0.0
    total = 0.0
    for (py, px) in points:
        total += haversine_km(lat, lon, py, px)
    return total / len(points)

def _minmax(values: List[float]) -> List[float]:
    """Min-max normalize to [0,1]. If all equal, return all 0.5."""
    if not values:
        return values
    vmin, vmax = min(values), max(values)
    if abs(vmax - vmin) < 1e-12:
        return [0.5 for _ in values]
    return [(v - vmin) / (vmax - vmin) for v in values]

def rank_hotels(
    hotels: List[Dict[str, Any]],
    day_centroids: List[Coord],
    *,
    min_rating: float = 4.0,
    min_candidates: int = 3,
    relax_to: float = 3.5,
    weights: Optional[Dict[str, float]] = None,
    return_debug: bool = False,
) -> List[str] | Tuple[List[str], List[Dict[str, Any]]]:
    """
    Rank hotels by a composite score:
      - distance to day centroids (closer is better)
      - rating
      - popularity (log(review_count+1))
    Returns sorted hotel IDs (best -> worst).
    If return_debug=True, also returns the scored rows.
    """
    if not hotels:
        return [] if not return_debug else ([], [])

    # 1) Pre-filter by rating (may relax).
    def _filter_by_rating(threshold: float) -> List[Dict[str, Any]]:
        return [h for h in hotels if float(h.get("rating", 0.0)) >= threshold]

    candidates = _filter_by_rating(min_rating)
    if len(candidates) < min_candidates:
        candidates = _filter_by_rating(relax_to)

    if not candidates:
        # Nothing meets thresholds; fall back to all.
        candidates = list(hotels)

    # 2) Compute features
    avg_dists = []
    ratings = []
    pops = []
    for h in candidates:
        lat, lon = float(h["lat"]), float(h["lon"])
        ad = _avg_distance_to_points(lat, lon, day_centroids)
        avg_dists.append(ad)
        ratings.append(float(h.get("rating", 0.0)))
        pops.append(math.log(float(h.get("review_count", 0)) + 1.0))

    # 3) Normalize (distance: smaller is better → we’ll use (1 - norm_dist))
    nd = _minmax(avg_dists)
    nr = _minmax(ratings)
    npop = _minmax(pops)

    # 4) Weighted score
    w = {"dist": 0.5, "rating": 0.35, "pop": 0.15}
    if weights:
        w.update(weights)

    scored = []
    for h, nd_i, nr_i, np_i, ad in zip(candidates, nd, nr, npop, avg_dists):
        score = w["dist"] * (1.0 - nd_i) + w["rating"] * nr_i + w["pop"] * np_i
        scored.append({
            "id": h["id"],
            "name": h.get("name"),
            "rating": float(h.get("rating", 0.0)),
            "review_count": int(h.get("review_count", 0)),
            "avg_dist_km": ad,
            "score": score
        })

    # 5) Sort deterministically: higher score, then rating, then reviews, then id.
    scored.sort(key=lambda r: (-r["score"], -r["rating"], -r["review_count"], str(r["id"])))
    ids_sorted = [r["id"] for r in scored]
    return (ids_sorted, scored) if return_debug else ids_sorted

