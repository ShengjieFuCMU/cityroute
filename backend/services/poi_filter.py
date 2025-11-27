# services/poi_filter.py
from __future__ import annotations
from typing import List, Dict, Any, Tuple

def apply_must_go(pois: List[Dict[str, Any]], only_must_go: bool) -> List[Dict[str, Any]]:
    if not only_must_go:
        return pois
    return [p for p in pois if bool(p.get("must_go"))]

def score_poi(p: Dict[str, Any]) -> float:
    # simple deterministic score: rating + 0.2*log1p(reviews); tie-break by id
    import math
    return float(p.get("rating", 0.0)) + 0.2 * math.log1p(float(p.get("review_count", 0)))

def cap_top_k(pois: List[Dict[str, Any]], k: int) -> Tuple[List[Dict[str, Any]], bool]:
    if k <= 0 or len(pois) <= k:
        return pois, False
    ranked = sorted(pois, key=lambda p: (-score_poi(p), str(p.get("id"))))
    return ranked[:k], True

