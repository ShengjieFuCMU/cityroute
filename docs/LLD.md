# CityRoute — Low-Level Design (LLD, Module-by-Module)

> Target design corresponding to the HLD modules. This document **specifies how each part will be built**: data structures, classes & methods, algorithms, and interfaces. API responses remain **IDs-only**; the UI may map `id → name` for display.

---

## 0) Notation & Conventions
- **Language/Stack:** Python 3.8, FastAPI, NumPy, scikit-learn; React (Vite) on the frontend.
- **Types:** `str | int | float | bool | list[T] | dict[str, T]` are Pythonic hints; data classes shown as JSON shapes.
- **Time windows:** strings `"HH:MM-HH:MM"` parsed to `(start_min, end_min)` since midnight.
- **Distance:** haversine (km); lon scaled by cos(mean_lat) for clustering.
- **IDs-only:** API never returns names for POI/Hotel/Restaurant.

---

## 1) Data Structures

### 1.1 Core Entities (JSON shape)
**POI**
```json
{ "id": "poi13", "name": "string", "lat": 40.44, "lon": -79.99, "rating": 4.5, "review_count": 320, "must_go": false }
```
**Hotel**
```json
{ "id": "h4", "name": "string", "lat": 40.45, "lon": -80.00, "rating": 4.2, "review_count": 210, "price_level": "$$" }
```
**Restaurant**
```json
{ "id": "r17", "name": "string", "lat": 40.44, "lon": -79.98, "rating": 4.3, "review_count": 540,
  "price_level": "$$", "diet_tags": ["vegetarian","vegan"],
  "open_lunch": "11:30-14:00", "open_dinner": "17:30-20:30" }
```
**DayPlan**
```json
{ "id": "day1", "visit_ids": ["poi17","poi16","poi2"], "lunch_id": "r23", "dinner_id": "r17", "total_time_minutes": 185 }
```
**Itinerary**
```json
{ "id": "it-001", "city": "Pittsburgh", "day_ids": ["day1","day2","day3"], "hotel_id": "h4", "warnings": [] }
```

### 1.2 Preferences (validated)
```json
{
  "days": 3,
  "detour_limit_minutes": 15,
  "diet_tags": ["vegetarian"],
  "price_range": "$$",
  "only_must_go": false,
  "max_pois_total": 40,
  "restaurant_radius_km": null
}
```
**Validation rules (400 on violation):** `days in [3..7]`, `max_pois_total in [1..40]`, `restaurant_radius_km == null or (0 < r ≤ 20)`.  
**Derived:** lunch=`(690, 840)`, dinner=`(1050, 1230)` minutes since midnight.

---

## 2) Module Specifications (classes, methods, algorithms)

### 2.1 UI Module (React)
**Components**
- `<PlannerForm />` (city, days, detour, diet, price, optional toggles).
- `<ItineraryPanel />` (shows itinerary_id, hotel_id, per-day visits, meals, total time).
- *(Planned)* `<NameToggle />` to show `name (id)` via a **local** id→name map from seeds.
**API calls (axios)**
- `POST /itinerary/generate`
- `POST /restaurants/auto_pick`
- `GET /itineraries/{id}`, `GET /days/{id}`
- `POST /export?fmt=json|csv`

---

### 2.2 Prefs/Policy Manager (planned)
**Class:** `class PolicyManager:`
- `validate_prefs(p: dict) -> None | raises HTTPException(400)`  
  - checks ranges for `days`, `max_pois_total`, `restaurant_radius_km`.
- `time_windows() -> dict`: returns `{ "lunch": (690,840), "dinner": (1050,1230) }`
- `detour_limit(p) -> int`: default 15 if missing.
- `apply_defaults(p) -> dict`: fills missing keys with defaults.

---

### 2.3 POI Filter Service (planned)
**Class:** `class POIFilter:`
- `filter(pois: list[POI], prefs) -> tuple[list[POI], list[str]]`  
  **Algorithm:**  
  1. If `only_must_go`, reduce to `[p for p in pois if p.must_go]`.  
  2. If `len(pois) > max_pois_total`, select Top-K by score `s = 0.7*rating + 0.3*log(review_count+1)`, with optional spatial coverage heuristic (pick k-means++ seeds then fill by score).  
  3. Return filtered POIs + `warnings` (e.g., `"trimmed from 52 to 40"`).

---

### 2.4 Clusterer
**Class:** `class Clusterer:`
- `cluster(pois: list[POI], k: int) -> dict` where result is `{ "clusters": list[list[POI]], "centroids": list[(lat,lon)], "warnings": list[str] }`
**Algorithm:**  
- Project to XY: `x = lon * cos(mean_lat)`, `y = lat`.  
- Run K-means (sklearn) with `n_init=10`, `random_state=42`.  
- If any cluster empty → re-init with k-means++ seeds; loop max 3 attempts.  
- Order clusters by centroid longitude for deterministic `day1..dayK`.

---

### 2.5 Router
**Class:** `class Router:`
- `route_day(pois: list[POI]) -> tuple[list[str], float]` returns `(visit_ids, total_minutes)`
**Algorithm:**  
1. Seed = POI closest to cluster centroid.  
2. **Nearest Neighbor** until all visited.  
3. **2-opt**: iterate all edge pairs; accept swap if total distance decreases by epsilon; stop when no improvement or `iters > 1000`.  
4. Time estimate = distance / `speed_kmh` (bounded 18–28), plus short per-visit overhead (e.g., 5 min).

---

### 2.6 HotelRanker
**Class:** `class HotelRanker:`
- `rank(hotels: list[Hotel], day_centroids: list[(lat,lon)]) -> str` returns `hotel_id`
**Scoring:**  
- `avgDist = mean(haversine(h, c) for c in day_centroids)`  
- Normalize features → `score = 0.45*(1-normAvgDist) + 0.40*normRating + 0.15*normLogReviews`  
- Pre-filter by `rating >= 3.5`. Tie-break by `id`.

---

### 2.7 Restaurant Radius Prefilter (planned)
**Class:** `class RestaurantRadius:`
- `apply(restaurants: list[Restaurant], centroid: (lat,lon), r_km: float|None) -> list[Restaurant]`  
  - If `r_km is None`, return input. Else keep `haversine(centroid, rest) <= r_km`.

---

### 2.8 RestaurantFinder
**Class:** `class RestaurantFinder:`
- `suggest_for_day(route_ids: list[str], restaurants: list[Restaurant], prefs, used_ids: set[str]) -> tuple[str|None, str|None, list[str]]`  
**Algorithm:**  
1. Compute candidate sets for lunch and dinner by **window**, **diet**, **price**; remove `used_ids`.  
2. For each candidate, compute **detour minutes** by inserting between any two consecutive visits and picking minimal added time.  
3. Score candidate `S = 0.60*normRating + 0.25*normLogReviews - 0.15*normDetour`.  
4. Pick argmax within `detour_limit`; if none, choose nearest feasible or return `None` with a note.  
5. Add chosen IDs to `used_ids` to enforce **no repeats** across days.

---

### 2.9 Exporter
**Class:** `class Exporter:`
- `export_json(itinerary_id: str) -> bytes`  
- `export_csv(itinerary_id: str) -> bytes`  
**Format:**  
- JSON: `{ itinerary, days[] }` with IDs only.  
- CSV: rows `(itinerary_id, day_id, visit_order, poi_id, lunch_id?, dinner_id?, total_time_minutes)`.

---

### 2.10 Storage
**Class:** `class InMemoryStore:`
- `save_itinerary(it: Itinerary, days: list[DayPlan]) -> None`  
- `get_itinerary(id: str) -> Itinerary`  
- `get_day(id: str) -> DayPlan`
**Note:** swap with SQLite later using the logical schema in §6.

---

## 3) API Interfaces

### 3.1 `POST /itinerary/generate`
**Request (target):**
```json
{
  "city": "Pittsburgh",
  "prefs": {
    "days": 3,
    "detour_limit_minutes": 15,
    "diet_tags": ["vegetarian"],
    "price_range": "$$",
    "only_must_go": false,
    "max_pois_total": 40,
    "restaurant_radius_km": null
  }
}
```
**Response:**
```json
{ "itinerary_id": "it-001", "day_ids": ["day1","day2","day3"], "hotel_id": "h4", "warnings": [] }
```
**Errors:** `400` invalid prefs; `422` malformed body.

### 3.2 `GET /itineraries/{id}`
**Response:** `{ "id": "it-001", "city": "Pittsburgh", "day_ids": [...], "hotel_id": "h4", "warnings": [] }`

### 3.3 `GET /days/{id}`
**Response:** `{ "id": "day1", "visit_ids": [...], "lunch_id": "r23", "dinner_id": "r17", "total_time_minutes": 185 }`

### 3.4 `POST /restaurants/auto_pick`
**Request:** `{ "itinerary_id": "it-001", "day_ids": ["day1","day2","day3"] }`  
**Response:** `{ "days": [ { "id": "day1", "lunch_id": "r23", "dinner_id": "r17", "notes": [] }, ... ] }`

### 3.5 `POST /export?fmt=json|csv`
**Response:** file bytes (download). `400` if unsupported fmt.

*(Optional)* `GET /healthz` → `{ "ok": true }`

---

## 4) Algorithmic Pseudocode

### 4.1 Router (NN + 2-opt)
```python
def route_day(points):
    start = argmin_distance_to_centroid(points)
    tour = [start]; unvisited = set(points) - {start}
    while unvisited:
        nxt = min(unvisited, key=lambda p: dist(tour[-1], p))
        tour.append(nxt); unvisited.remove(nxt)
    improved = True; iters = 0
    while improved and iters < 1000:
        improved = False; iters += 1
        for i in range(1, len(tour)-2):
            for j in range(i+1, len(tour)-1):
                if gain_if_2opt_swap(tour, i, j) > 0:
                    apply_2opt_swap(tour, i, j); improved = True
    return ids(tour), minutes(total_distance(tour))
```

### 4.2 Restaurant detour
```python
def min_detour_minutes(route_points, candidate):
    best = +inf
    for i in range(len(route_points)-1):
        a, b = route_points[i], route_points[i+1]
        detour = dist(a, candidate) + dist(candidate, b) - dist(a, b)
        best = min(best, detour)
    return minutes(best / speed_kmh)
```

---

## 5) Error Handling & Messages

| Code | When | Example detail |
|---|---|---|
| **400** | `days` outside [3..7] | "days must be between 3 and 7" |
| **400** | `max_pois_total` invalid | "max_pois_total must be 1..40" |
| **400** | `restaurant_radius_km` invalid | "restaurant_radius_km must be > 0" |
| **422** | Malformed JSON | Pydantic validation error |
| **409** | Locks make route infeasible (future) | "route infeasible with current locks" |

**Principle:** user-caused errors → 4xx with clear messages; internal errors never leak stack traces.

---

## 6) Persistence (future DB logical schema)
- `poi(id PK, name, lat, lon, rating, review_count, must_go)`
- `hotel(id PK, name, lat, lon, rating, review_count, price_level)`
- `restaurant(id PK, name, lat, lon, rating, review_count, price_level, diet_tags, open_lunch, open_dinner)`
- `itinerary(id PK, city, hotel_id, created_at)`
- `day_plan(id PK, itinerary_id, total_time_minutes)`
- `day_plan_visits(day_id, order_idx, poi_id)`  (PK: day_id+order_idx)

Indexes on `(day_id, order_idx)`; FKs enforce referential integrity.

---

## 7) Determinism & Config
- `random_state = 42` (K-means). Tie-breaks by id.
- Tunables: `detour_limit_minutes`, `min_hotel_rating`, `speed_kmh_bounds`, lunch/dinner windows.
- Feature flags: `only_must_go`, `max_pois_total`, `restaurant_radius_km`.

---

## 8) Interfaces Between Modules (call graph, simplified)

```
PlannerService.generate(prefs)
  → PolicyManager.validate_prefs
  → POIFilter.filter
  → Clusterer.cluster
  → Router.route_day (for each cluster)
  → HotelRanker.rank
  → Storage.save_itinerary

PlannerService.auto_pick(itinerary_id, day_ids)
  → Storage.get_day
  → RestaurantRadius.apply (if set)
  → RestaurantFinder.suggest_for_day
  → Storage.save_day
```
