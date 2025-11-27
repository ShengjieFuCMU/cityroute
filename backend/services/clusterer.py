# backend/services/clusterer.py
from __future__ import annotations
import math
import random
from typing import Dict, List, Tuple, Any, Optional

try:
    from sklearn.cluster import KMeans  # optional (faster)
    _HAS_SK = True
except Exception:
    _HAS_SK = False

# ---- Helpers ----

def _lon_scale(mean_lat_deg: float) -> float:
    """Scale factor so that 1 degree lon ~= 1 degree lat at the city's latitude."""
    return math.cos(math.radians(mean_lat_deg))

def _to_xy(lat: float, lon: float, scale_x: float) -> Tuple[float, float]:
    # x ~ lon * cos(phi), y ~ lat
    return (lon * scale_x, lat)

def _centroid_xy(points_xy: List[Tuple[float, float]]) -> Tuple[float, float]:
    if not points_xy:
        raise ValueError("Empty points for centroid")
    sx = sum(p[0] for p in points_xy)
    sy = sum(p[1] for p in points_xy)
    n = len(points_xy)
    return (sx / n, sy / n)

def _xy_to_latlon(x: float, y: float, scale_x: float) -> Tuple[float, float]:
    lat = y
    lon = x / scale_x if scale_x != 0 else 0.0
    return (lat, lon)

# ---- Main API ----

def cluster_pois_kmeans(
    pois: List[Dict[str, Any]],
    k: int,
    *,
    random_state: int = 42,
    max_iter: int = 100,
    n_init: int = 10,
    must_go_ratio_warn: float = 0.60,
) -> Dict[str, Any]:
    """
    Cluster POIs into k geographic groups using k-means.
    Inputs:
      - pois: [{id, name, lat, lon, rating, review_count, must_go: bool}, ...]
      - k: target number of clusters (days)
    Returns:
      {
        "clusters": [
           { "day_id": "day1", "poi_ids": [...], "centroid": (lat, lon) },
           ...
        ],
        "warnings": [ ... ]
      }
    """
    if not pois:
        return {"clusters": [], "warnings": ["No POIs provided."]}

    n = len(pois)
    k = max(1, min(k, n))  # cap
    mean_lat = sum(p["lat"] for p in pois) / n
    sx = _lon_scale(mean_lat)

    # Build XY array
    pts_xy = [_to_xy(p["lat"], p["lon"], sx) for p in pois]

    # ---- Use sklearn if available ----
    if _HAS_SK:
        import numpy as np
        X = np.array(pts_xy, dtype=float)
        km = KMeans(n_clusters=k, random_state=random_state, n_init=n_init, max_iter=max_iter)
        labels = km.fit_predict(X)  # [0..k-1]
        centers = km.cluster_centers_  # shape (k,2)
        centroids_latlon = [_xy_to_latlon(cx, cy, sx) for (cx, cy) in centers]
    else:
        # ---- Very small pure-Python Lloyd's algorithm ----
        random.seed(random_state)
        # init centers as random distinct points
        centers = random.sample(pts_xy, k)
        labels = [0] * n

        def assign():
            nonlocal labels
            new_labels = []
            for (x, y) in pts_xy:
                # argmin distance^2 to centers
                best = 0
                bestd = float("inf")
                for idx, (cx, cy) in enumerate(centers):
                    d = (x - cx) ** 2 + (y - cy) ** 2
                    if d < bestd:
                        bestd = d
                        best = idx
                new_labels.append(best)
            labels = new_labels

        def update():
            nonlocal centers
            changed = False
            for j in range(k):
                group = [pts_xy[i] for i in range(n) if labels[i] == j]
                if not group:
                    # re-seed empty cluster to a random point
                    centers[j] = random.choice(pts_xy)
                    changed = True
                else:
                    cx, cy = _centroid_xy(group)
                    if (cx, cy) != centers[j]:
                        centers[j] = (cx, cy)
                        changed = True
            return changed

        for _ in range(max_iter):
            assign()
            if not update():
                break

        centroids_latlon = [_xy_to_latlon(cx, cy, sx) for (cx, cy) in centers]

    # Build cluster lists
    clusters_idx: List[List[int]] = [[] for _ in range(k)]
    for i, lab in enumerate(labels):
        clusters_idx[lab].append(i)

    # Stable order by centroid longitude (east->west) or size
    # (Choose a consistent order to make "day1..dayK" deterministic.)
    order = sorted(range(k), key=lambda j: (centroids_latlon[j][1], centroids_latlon[j][0]))
    day_map = {}
    clusters_out = []
    warnings: List[str] = []

    avg_size = math.ceil(n / k)

    for rank, j in enumerate(order, start=1):
        day_id = f"day{rank}"
        day_map[j] = day_id
        poi_ids = [pois[i]["id"] for i in clusters_idx[j]]
        clusters_out.append({
            "day_id": day_id,
            "poi_ids": poi_ids,
            "centroid": (round(centroids_latlon[j][0], 6), round(centroids_latlon[j][1], 6))
        })

        # Must-go density heuristic warning
        if poi_ids:
            mg = sum(1 for i in clusters_idx[j] if bool(pois[i].get("must_go")))
            ratio = mg / len(poi_ids)
            if ratio >= must_go_ratio_warn and len(poi_ids) >= (avg_size + 2):
                warnings.append(
                    f"High must-go density in {day_id} ({mg}/{len(poi_ids)}). "
                    f"Consider adding a day or unmarking some must-go items."
                )

    return {"clusters": clusters_out, "warnings": warnings}

