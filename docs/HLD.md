# CityRoute — High-Level Design (HLD)
---
## 1. Context & Goals
- **Goal.** Plan a **3–7 day** city trip (Pittsburgh) that (a) clusters POIs by day, (b) routes visits within a day, (c) suggests a hotel, and (d) auto-picks lunch/dinner.
- **Scope (target).**
  - City: Pittsburgh (midterm), single itinerary per request.
  - Inputs: days, detour limit, diet tags, price range; **planned** user prefs include `only_must_go`, `max_pois_total`, `restaurant_radius_km`.
  - Outputs: **IDs-only** API (privacy by design). UI may optionally show `name (id)` via local lookup.
- **Constraints.**
  - **Days** ∈ **[3..7]**
  - **Total POIs** ≤ **40**
  - Lunch window **11:30–14:00**, Dinner **17:30–20:30**
  - Default detour limit **≤ 15 minutes**
  - Plan time target **≤ 10 s** on a developer laptop (≤40 POIs)

---

## 2. Architecture Overview
**Three-tier, local-first**:

```
[React (Vite) UI]
        ↓ axios
[FastAPI service]  ─── uses ───► [Seed data + In-memory storage]
```

- **UI (React/Vite).** Thin form + results; optional id→name display.
- **API (FastAPI).** Orchestrates planner pipeline (filter → cluster → route → rank hotel → meals).
- **Data.** Seed CSVs (`pois`, `hotels`, `restaurants`) loaded at startup; in-memory itinerary storage for demo.

**Diagrams**
- Architecture: `../diagrams/architecture.svg`
- Use Case: `../diagrams/usecase-cityroute.svg`
- Sequences: `../diagrams/seq-generate.svg`, `../diagrams/seq-autopick.svg`, `../diagrams/seq-regenerate.svg`

---

## 3. Modules & Responsibilities
- **UI Module**
  - Inputs: city, days, detour, diet tags, price; actions: Generate, Auto-Pick, Export.
  - Display: itinerary id, hotel id, per-day visit ids, meals, total time.
  - *(Planned)* Toggle “Show Names” → id→name mapping on the client only.

- **Prefs/Policy Manager** *(planned)*
  - Centralizes all constraints (days range, ≤40 POIs, time windows, detour limit).
  - Interprets `only_must_go`, `max_pois_total`, `restaurant_radius_km`.

- **POI Filter Service** *(planned)*
  - Applies `only_must_go` and caps total POIs to `max_pois_total` **before** clustering.
  - Policy for capping: pick by rating/popularity and/or spatial coverage; records a warning if trimming occurs.

- **Clusterer**
  - K-means (K = days) in lat/lon space (lon scaled by cos(mean_lat)).
  - Mitigations: re-seed empty clusters; warn on “must-go density” issues.

- **Router**
  - Build visit order per day via Nearest-Neighbor + 2-opt improvement; deterministic tie-breakers.

- **HotelRanker**
  - Composite score = distance to day centroids + rating + popularity (log review count); pre-filter by min rating.

- **Restaurant Radius Prefilter** *(planned)*
  - Filter candidates within `restaurant_radius_km` of a day centroid **prior** to scoring.

- **RestaurantFinder**
  - Filter by open window + diet + price + detour ≤ limit; ensure **no repeat** across days; fallback to nearest feasible with notes.

- **Exporter**
  - JSON/CSV exports (IDs only). *(PDF optional stub.)*

- **Storage**
  - Read seeds; persist itineraries/day plans in memory (swap to DB later).

---

## 4. Key Interactions (Target)
- **Generate**
  1) UI → `POST /itinerary/generate` (city, prefs)  
  2) Prefs/Policy validation → **POI Filter Service** (only_must_go / max_pois_total)  
  3) Clusterer (K=days) → Router per day → HotelRanker  
  4) Save Itinerary + DayPlans → return IDs

- **Auto-Pick Meals**
  1) UI → `POST /restaurants/auto_pick` (itinerary, day_ids)  
  2) **Restaurant Radius Prefilter** (if set) → RestaurantFinder (windows/diet/price/detour, no repeats)  
  3) Update DayPlans (IDs) + notes

- **Export**
  1) UI → `POST /export?fmt=json|csv`  
  2) Build artifact (IDs-only) → download/return link

---

## 5. Non-Functional Requirements (NFRs)
- **Performance:** ≤ **10 s** for ≤ **40** POIs end-to-end on a laptop.
- **Privacy:** API returns **IDs only**; names are UI-side lookups.
- **Determinism/Reproducibility:** fixed `random_state` for K-means; stable sorting for ties.
- **Deployability:** single machine; no live external APIs in midterm scope.
- **Observability:** minimal logging of timings and warnings.

---

## 6. Risks & Mitigations
- **No feasible restaurant** in window/detour → fallback to nearest feasible or leave null with **explicit note**.
- **Over-constrained POIs** (must-go too many) → warning suggests adding days or relaxing filters.
- **Heuristic routing** (not optimal) → documented expectations; future: iterate depth or add SA/GA as optional.

---

## 7. Roadmap Notes (Post-Midterm)
- Add persistent DB (SQLite) + CRUD for saved itineraries.
- Add map view with markers and hover details (UI).
- Add locks (fixed start/visit) and conflict reporting (409).

---

## Appendix — Status (v1 Demo)
- Implemented: Generate (cluster/route/hotel), Auto-Pick (windows/diet/price/detour/no-repeat), Export (JSON/CSV), IDs-only API, in-memory storage.
- Known gaps (v1): no strict days-range rejection; schema mistakes can produce 500s; planned filters (`only_must_go`, `max_pois_total`, `restaurant_radius_km`) and UI name toggle not yet implemented.
