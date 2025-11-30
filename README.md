# CityRoute v1 – Midterm Demo

CityRoute is a **single-city** trip planner (Pittsburgh for the midterm) that:

- Clusters POIs into **3–7× day plans**,
- Orders visits per day with a fast route (Nearest-Neighbor + 2-opt),
- Suggests a **convenient hotel** near day centroids,
- Auto-picks **lunch** and **dinner** per day (open hours, diet/price, detour limit, no repeats),
- Exports the plan as **JSON** and **CSV**.

This README documents **Version 1 (v1)** used for the demo and applied project.

---

## 0) Prerequisites

- **Python 3.8+**
- **Node.js 18+** and **npm**
- macOS / Windows / Linux supported

---

## 1) Repository Layout

CityRoute/

    ├─ backend/
    │  ├─ app.py                 # FastAPI endpoints
    │  ├─ data/                  # seed CSVs (POIs, Hotels, Restaurants)
    │  │  ├─ pois.csv
    │  │  ├─ hotels.csv
    │  │  └─ restaurants.csv
    │  ├─ services/              # planner, clusterer, router, hotel_ranker, restaurants
    │  ├─ storage/               # in-memory stores
    │  ├─ utils/                 # geo/time helpers
    │  ├─ scripts/               # demo_run.py etc.
    │  ├─ tests/                 # pytest suite
    │  ├─ pytest.ini
    │  └─ requirements.txt
    ├─ frontend/
    │  ├─ src/
    │  │  ├─ App.jsx
    │  │  ├─ api.js
    │  │  ├─ main.jsx
    │  │  ├─ App.css
    │  │  └─ index.css
    │  ├─ .env                   # VITE_API_URL=http://127.0.0.1:8000
    │  ├─ index.html
    │  ├─ package.json
    │  └─ vite.config.js
    ├─ docs/                     # SRS, diagrams, examples, test plan, slides
    ├─ diagrams/                 # PlantUML + exported SVGs
    ├─ README.md                 # this file
    └─ README_v1.md              # original v1 midterm README snapshot

---

## 2) What v1 Delivers (Scope)

- **City:** Pittsburgh  
- **Days:** 3–7 (validated)  
- **≤ 40 POIs** per itinerary (guardrail)  
- **IDs-only API** (matches SRS): `Itinerary` + `DayPlan` with `visit_ids`, `lunch_id`, `dinner_id`, `hotel_id`  
- **Hotel suggestion:** ranked by proximity to day centroids + rating + log(reviews)  
- **Restaurant auto-pick:** open windows, diet/price filters, detour limit; **no repeats across days** if avoidable  
- **Exports:** JSON (structured), CSV (1 row per day)

> `total_time_minutes` per day in v1 = **estimated travel time only** between POIs (straight-line distance → minutes); no visiting duration yet.

---

## 3) Running Locally

### 3.1 Backend (FastAPI)

    cd backend
    python -m venv .venv

    # macOS / Linux:
    source .venv/bin/activate
    # Windows PowerShell:
    # .venv\Scripts\Activate.ps1

    pip install -r requirements.txt
    uvicorn app:app --reload    # http://127.0.0.1:8000

- Swagger UI: http://127.0.0.1:8000/docs  

### 3.2 Frontend (Vite + React)

    cd frontend
    npm install

This repo already includes `frontend/.env` with:

    VITE_API_URL=http://127.0.0.1:8000

If `.env` is missing, create it with that line.

Then start the dev server:

    npm run dev    # http://localhost:5173

---

## 4) Demo Flow (UI)

1. Open `http://localhost:5173`.
2. Fill **City**, **Days**, optional **Diet tags** (e.g., `vegetarian|vegan`), **Price** (`$`, `$$`, `$$$`), **Detour limit** (minutes).
3. Click **Generate** → shows itinerary id, hotel id, and day ids.
4. Click **Auto-Pick Meals** → each day card shows `visit_ids`, `lunch_id`, `dinner_id`, and `total_time_minutes`.
5. Click **Export JSON** or **Export CSV** to download files.

If the backend restarts, in-memory data resets → click **Generate** again.

---

## 5) Quick API Test (CLI)

With the server running (`uvicorn app:app --reload`):

**A) Generate itinerary (uses seed CSVs)**

    curl -s -X POST http://127.0.0.1:8000/itinerary/generate \
         -H "Content-Type: application/json" \
         -d '{"city":"Pittsburgh","prefs":{"days":3,"travel_mode":"drive","detour_limit_minutes":20}}'

**B) Auto-Pick meals (override detour limit if needed)**

    curl -s -X POST http://127.0.0.1:8000/restaurants/auto_pick \
         -H "Content-Type: application/json" \
         -d '{"itinerary_id":"it-001","detour_limit_min":25}'

**C) Export JSON**

    curl -s -X POST http://127.0.0.1:8000/export \
         -H "Content-Type: application/json" \
         -d '{"itinerary_id":"it-001","format":"json"}'

**D) Export CSV (returns `csv_text`; frontend downloads as file)**

    curl -s -X POST http://127.0.0.1:8000/export \
         -H "Content-Type: application/json" \
         -d '{"itinerary_id":"it-001","format":"csv"}'

(Replace `it-001` / `day1` with the IDs you actually received.)

---

## 6) API Endpoints (v1)

- **POST** `/itinerary/generate`  
  Req: `{ city, prefs, locks? }`  
  Res: `{ itinerary_id, day_ids[], hotel_id?, warnings[] }`

- **POST** `/restaurants/auto_pick`  
  Req: `{ itinerary_id, day_ids?, detour_limit_min? }`  
  Res: `{ days: [{ id, lunch_id?, dinner_id?, notes[] }] }`

- **GET** `/itineraries/{id}`  
  Res: IDs-only itinerary (`day_ids`, `hotel_id`, `prefs`, `warnings`)

- **GET** `/days/{id}`  
  Res: `DayPlan` (IDs-only: `visit_ids`, `lunch_id`, `dinner_id`, `total_time_minutes`)

- **POST** `/export`  
  Req: `{ itinerary_id, format: "json" | "csv" }`  
  Res: JSON payload or `{ filename, content_type, csv_text }` for CSV

---

## 7) Seed CSV Formats (Expected Columns)

**backend/data/pois.csv**

    id,name,lat,lon,rating,review_count,must_go

**backend/data/hotels.csv**

    id,name,lat,lon,rating,review_count,price_level

**backend/data/restaurants.csv**

    id,name,lat,lon,rating,review_count,price_level,diet_tags,open_lunch,open_dinner

Coordinate sanity (Pittsburgh):

- `lat` ~ 40.30–40.60  
- `lon` ~ −80.10 … −79.80  (note the **minus** sign)

---

## 8) Business Rules (v1)

- Days ∈ [3, 7]
- ≤ 40 POIs per itinerary
- Meal windows:
  - Lunch **11:30–14:00**
  - Dinner **17:30–20:30**
- Detour limit default 15 min (can override)
- Diet / price filters enforced when provided
- No restaurant repeats across days unless unavoidable (adds a clear note)
- API is IDs-only to match SRS & diagrams

---

## 9) Troubleshooting

- **Frontend can’t reach backend** → check `frontend/.env` contains:

      VITE_API_URL=http://127.0.0.1:8000

  Restart `npm run dev` after changes.

- **404 itinerary not found** → backend restarted; click **Generate** again.  
- **Huge detour notes** → try `detour_limit_min` 20–30; verify restaurant coordinates.  
- **CSV not downloading in browser** → in v1, server returns `csv_text`; the frontend saves it as a file.

---

## 10) Clean Zip for Submission (optional)

From the repo root:

    # Optional: tag this version
    git add .
    git commit -m "CityRoute v1 (midterm demo)"
    git tag v1.0.0

    # Create zip without node_modules / venv
    zip -r CityRoute_v1_midterm.zip \
        backend frontend docs diagrams data \
        -x "frontend/node_modules/*" -x "backend/.venv/*" -x "*/.DS_Store"

---

## 11) Next Steps (v2 Ideas)

- Pick POIs
- Introduce per-stop durations feature
- Restaurant radius pre-filter around day centroid
- Map view (Leaflet)
- Optional DB (Postgres/PostGIS) and persistence

---

## 12) License / Contact

- Course project — educational use only.  

