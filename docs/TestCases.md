# CityRoute — Test Cases (Design Validation for Target System)


**System Under Test (SUT):** CityRoute — Pittsburgh trip planner (3–7 days), clusters POIs by day, routes visits, suggests a hotel, auto‑picks lunch/dinner.  
**Tech:** Backend FastAPI (Python 3.8), Frontend React (Vite), in‑memory storage; seeds in `backend/data/seeds/`.  
**Privacy:** API is **IDs‑only**; the UI may optionally show `name (id)` via local lookup.  
**Constraints:** Days ∈ [3..7]; ≤40 POIs total; lunch 11:30–14:00; dinner 17:30–20:30; default detour ≤15 min.  
**Traceability:** FR1 Generate, FR2 Hotel, FR3 Auto‑Pick, FR4 Export; NFR1 Performance, NFR2 Privacy, NFR3 Determinism.

---

## Pre‑Test Setup (common)
1) Backend at `http://127.0.0.1:8000`, Frontend at `http://127.0.0.1:5173`.  
2) Seeds present: `backend/data/seeds/{pois.csv, hotels.csv, restaurants.csv}`.  
3) Defaults unless noted: detour=15, diet=none, price=any.  
4) API docs (Swagger) reachable at `/docs`.

> **Pass/Fail policy:** Mark **Pass** only if every expected item is met exactly. Any deviation → **Fail**.

---

## UC‑Generate — Main & Exception Flows

**Test Case Number:** TC‑G1  
**Revision:** 1.0 **Author:** <Your Name> **Date Conducted:** <Date>  
**Description:** Generate itinerary (happy path, 3 days).  
**Use Case:** UC‑Generate **Flow:** Main

| User Action | Expected Results (Target) | P/F | Execution Status | Comment |
|---|---|---|---|---|
| Enter City=Pittsburgh, Days=3, Detour=15; click **Generate**. | API returns **IDs‑only** payload with `itinerary_id`, `day_ids=["day1","day2","day3"]`, and `hotel_id`. No error banner. |  | Planned | FR1, FR2, NFR2 |
| Open `/itineraries/{itinerary_id}` and `/days/{day_id}`. | Schemas match LLD: a day has `visit_ids[]`, optional `lunch_id`/`dinner_id`, and numeric `total_time_minutes`. |  | Planned | FR1, NFR2 |

---

**Test Case Number:** TC‑G2  
**Description:** Reject invalid days (below minimum).  
**Flow:** Exception

| User Action | Expected Results (Target) | P/F | Execution Status | Comment |
|---|---|---|---|---|
| Enter Days=2; click **Generate**. | API returns **HTTP 400** with detail `"days must be between 3 and 7"`. No itinerary created. |  | Planned | FR1 (validation) |

---

**Test Case Number:** TC‑G3  
**Description:** Reject invalid days (above maximum).  
**Flow:** Exception

| User Action | Expected Results (Target) | P/F | Execution Status | Comment |
|---|---|---|---|---|
| Enter Days=8; click **Generate**. | API returns **HTTP 400** with detail `"days must be between 3 and 7"`. No itinerary created. |  | Planned | FR1 (validation) |

---

**Test Case Number:** TC‑G4  
**Description:** POI cap at boundary (exactly 40).  
**Flow:** Main

| User Action | Expected Results (Target) | P/F | Execution Status | Comment |
|---|---|---|---|---|
| Ensure available POIs ≤40; Generate with Days=3–5. | Plan completes; total POIs considered ≤40; warnings empty or informational. |  | Planned | FR1, NFR1 |

---

**Test Case Number:** TC‑G5  
**Description:** Over‑cap POIs (>40) handled by policy.  
**Flow:** Alternate

| User Action | Expected Results (Target) | P/F | Execution Status | Comment |
|---|---|---|---|---|
| Generate where raw POIs >40. | System **trims to 40** prior to clustering and returns a **warning** (e.g., `"trimmed from 52 to 40"`). *(If your policy is reject, change here to 400 and keep consistent with LLD.)* |  | Planned | FR1 |

---

**Test Case Number:** TC‑G6  
**Description:** Deterministic outputs for same inputs.  
**Flow:** Main

| User Action | Expected Results (Target) | P/F | Execution Status | Comment |
|---|---|---|---|---|
| Run **Generate** twice with identical inputs. | Same number of days and stable visit ordering (within heuristic ties); documented determinism (fixed random_state). |  | Planned | NFR3 |

---

## UC‑AutoPick — Main & Exception Flows

**Test Case Number:** TC‑M1  
**Description:** Auto‑pick meals for all days (typical).  
**Flow:** Main

| User Action | Expected Results (Target) | P/F | Execution Status | Comment |
|---|---|---|---|---|
| Click **Auto‑Pick** or POST `/restaurants/auto_pick`. | For each day: `lunch_id` and `dinner_id` chosen when feasible; `notes` empty or informative. |  | Planned | FR3, NFR2 |
| Review all days for duplicates. | No restaurant ID repeats across different days; if constraints force reuse, a **note** explains the relaxation. |  | Planned | FR3 |

---

**Test Case Number:** TC‑M2  
**Description:** Respect lunch/dinner windows.  
**Flow:** Alternate

| User Action | Expected Results (Target) | P/F | Execution Status | Comment |
|---|---|---|---|---|
| Use a day with a dinner‑only candidate; run **Auto‑Pick**. | Lunch remains unset or a feasible lunch is chosen; dinner selected appropriately; **note** explains any relaxation. |  | Planned | FR3 |

---

**Test Case Number:** TC‑M3  
**Description:** Enforce detour limit (≤15 min).  
**Flow:** Alternate

| User Action | Expected Results (Target) | P/F | Execution Status | Comment |
|---|---|---|---|---|
| Run **Auto‑Pick** with detour=15. | Chosen restaurants have detour ≤15 min; if none feasible, nearest‑feasible or null with **note**. |  | Planned | FR3 |

---

**Test Case Number:** TC‑M4  
**Description:** Diet/price filters reduce candidate set.  
**Flow:** Alternate

| User Action | Expected Results (Target) | P/F | Execution Status | Comment |
|---|---|---|---|---|
| Set `diet_tags=["vegan"]` and `price_range="$$$"`; Generate + **Auto‑Pick**. | Meals chosen respecting diet+price; if none satisfy constraints, meal remains null or nearest‑feasible chosen with **note**. |  | Planned | FR3 |

---

**Test Case Number:** TC‑M5  
**Description:** Restaurant radius prefilter (planned).  
**Flow:** Alternate

| User Action | Expected Results (Target) | P/F | Execution Status | Comment |
|---|---|---|---|---|
| Set `restaurant_radius_km=5`; run **Auto‑Pick**. | All selected restaurants lie within 5 km of each day’s centroid; otherwise null or relaxed with **note**. |  | Planned | FR3 (planned) |

---

## UC‑Export — Main Flows

**Test Case Number:** TC‑E1  
**Description:** Export JSON (IDs‑only).  
**Flow:** Main

| User Action | Expected Results (Target) | P/F | Execution Status | Comment |
|---|---|---|---|---|
| Click **Export JSON**. | Downloaded file contains itinerary + days; **IDs‑only**; fields match LLD schema. |  | Planned | FR4, NFR2 |

---

**Test Case Number:** TC‑E2  
**Description:** Export CSV (IDs‑only).  
**Flow:** Main

| User Action | Expected Results (Target) | P/F | Execution Status | Comment |
|---|---|---|---|---|
| Click **Export CSV**. | CSV has tidy columns `(itinerary_id, day_id, visit_order, poi_id, lunch_id?, dinner_id?, total_time_minutes)`; opens without error; no names leaked. |  | Planned | FR4, NFR2 |

---

## API Contract & Error Handling

**Test Case Number:** TC‑A1  
**Description:** `/itinerary/generate` schema conformance.  
**Flow:** Main

| User Action | Expected Results (Target) | P/F | Execution Status | Comment |
|---|---|---|---|---|
| POST a valid body to `/itinerary/generate`. | Response matches LLD exactly; no extra fields; `warnings` is an array of strings. |  | Planned | FR1, NFR2 |

---

**Test Case Number:** TC‑A2  
**Description:** `/days/{id}` schema conformance.  
**Flow:** Main

| User Action | Expected Results (Target) | P/F | Execution Status | Comment |
|---|---|---|---|---|
| GET `/days/{day_id}`. | Response includes `visit_ids[]`, `total_time_minutes` (number), optional `lunch_id`/`dinner_id`; no names. |  | Planned | FR1, FR3, NFR2 |

---

**Test Case Number:** TC‑A3  
**Description:** `/restaurants/auto_pick` schema conformance.  
**Flow:** Main

| User Action | Expected Results (Target) | P/F | Execution Status | Comment |
|---|---|---|---|---|
| POST `{ itinerary_id, day_ids[] }`. | Returns `{ "days": [ { "id": <ID>, "lunch_id": <ID|null>, "dinner_id": <ID|null>, "notes": [] } ] }`. |  | Planned | FR3, NFR2 |

---

**Test Case Number:** TC‑A4  
**Description:** Malformed request yields validation error (not 500).  
**Flow:** Exception

| User Action | Expected Results (Target) | P/F | Execution Status | Comment |
|---|---|---|---|---|
| POST `/itinerary/generate` with malformed JSON (types/fields missing). | API returns **400/422** with a human‑readable message; no 500; no stack trace. |  | Planned | Robustness |

---

## Non‑Functional Requirements

**Test Case Number:** TC‑N1  
**Description:** Performance ≤10 s (≤40 POIs).  
**Flow:** NFR

| User Action | Expected Results (Target) | P/F | Execution Status | Comment |
|---|---|---|---|---|
| Time a single **Generate** end‑to‑end with ~40 POIs. | Elapsed time **≤ 10 s** on a developer laptop. |  | Planned | NFR1 |

---

**Test Case Number:** TC‑N2  
**Description:** Privacy — IDs‑only API.  
**Flow:** NFR

| User Action | Expected Results (Target) | P/F | Execution Status | Comment |
|---|---|---|---|---|
| Inspect responses from Generate, Days, Auto‑Pick. | **No `name` fields** are returned in API; only IDs/numerics. |  | Planned | NFR2 |

---

**Test Case Number:** TC‑N3  
**Description:** Determinism / reproducibility.  
**Flow:** NFR

| User Action | Expected Results (Target) | P/F | Execution Status | Comment |
|---|---|---|---|---|
| Repeat **Generate** with identical inputs. | Outputs are stable within tie rules (fixed seed, deterministic ties). |  | Planned | NFR3 |

---

## Usability & Safety Nets

**Test Case Number:** TC‑U1  
**Description:** Over‑constraints produce actionable warnings.  
**Flow:** Alternate

| User Action | Expected Results (Target) | P/F | Execution Status | Comment |
|---|---|---|---|---|
| Use must‑go density too high or strict diet+price+radius. | API/UI returns human‑readable warnings suggesting relaxing filters or adding days. |  | Planned | UX clarity |

---

**Test Case Number:** TC‑U2  
**Description:** Export availability and integrity.  
**Flow:** Main

| User Action | Expected Results (Target) | P/F | Execution Status | Comment |
|---|---|---|---|---|
| Export JSON, then CSV. | Both downloads succeed; files open; headers/fields correct; **no names leaked**. |  | Planned | FR4, NFR2 |

---

## Coverage Matrix (HLD Modules ↔ Tests)
- **Prefs/Policy Manager:** TC‑G2, TC‑G3, TC‑G5, TC‑M5  
- **POI Filter Service:** TC‑G5  
- **Clusterer:** TC‑G1, TC‑N3  
- **Router:** TC‑G1, TC‑N3  
- **HotelRanker:** TC‑G1  
- **Restaurant Radius Prefilter:** TC‑M5  
- **RestaurantFinder:** TC‑M1..M4  
- **Exporter:** TC‑E1, TC‑E2  
- **Privacy/IDs‑only:** TC‑N2  
- **Error handling:** TC‑A4  
- **Performance:** TC‑N1

---

## Notes
- Keep **Expected Results** aligned with LLD. If you change a policy (e.g., trim vs reject at >40 POIs), update both LLD and this file.  
- For final project execution, fill **P/F** and set **Execution Status = Executed**, optionally linking to evidence (screens/JSON).

