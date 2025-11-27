
# CityRoute — Ethical and Societal Effects (v1)

**Scope (v1):** IDs-only outputs; Pittsburgh-only; seed CSV data; local, in-memory storage.

## Privacy & Data Minimization
CityRoute v1 returns **IDs-only** and uses curated **seed files** for POIs/hotels/restaurants. It does not collect or persist any personal user data or live location traces. In-memory storage is reset on restart. This minimizes privacy risk while enabling the core planning functions.

## Algorithmic Transparency & Fairness
Hotel and restaurant suggestions use transparent, heuristic scoring (distance-to-day-centroids, ratings, review counts, detour). The meal picker respects windows (lunch/dinner), diet tags, and price range, and avoids repeats across days. When constraints cannot be met (e.g., no open restaurants within the detour limit), CityRoute clearly notes the **fallback** (e.g., “relaxed detour”) to avoid silent bias. Diet tags are matched as provided in seeds; users should verify allergy/cross-contamination concerns directly with venues.

## Safety, Accuracy & Responsibility
Travel times and open hours are **planning-grade** estimates (no real-time traffic or live hours); users should verify details before travel. CityRoute assists with high-level organization, not navigation or safety-critical guidance. Future work includes improving accessibility (e.g., wheelchair-friendly metadata), and adding clearer explanations when recommendations are relaxed due to constraints.
