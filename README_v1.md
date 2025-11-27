# CityRoute v1 — Midterm Demo

CityRoute is a single‑city trip planner (Pittsburgh for the midterm) that:
- Clusters POIs into **3–7** day plans,
- Orders visits per day with a fast route (nearest‑neighbor + 2‑opt),
- Suggests a **convenient hotel** near day centroids,
- Auto‑picks **lunch** and **dinner** per day with basic constraints,
- Exports the plan as **JSON** and **CSV**.

This README documents **Version 1 (v1)** used for the midterm demo.

---

## Stack

**Backend**
- Python 3.8
- FastAPI + Uvicorn
- NumPy, scikit‑learn (k‑means)
- In‑memory storage (no DB)

**Frontend**
- React (Vite)
- axios

**Data**
- Seed CSVs in `backend/data/`: `pois.csv`, `hotels.csv`, `restaurants.csv`

---

## What v1 Delivers (Scope)

- **City:** Pittsburgh
- **Days:** 3–7 (validated)
- **≤ 40 POIs** total
- **IDs‑only API** (matches SRS): `Itinerary`, `DayPlan` with `visit_ids`, `lunch_id`, `dinner_id`
- **Hotel suggestion:** rank by proximity to day centroids + rating + log(reviews)
- **Restaurant auto‑pick:** respects open windows, diet/price filters, detour limit
  - Avoids **repeats across days** unless unavoidable (adds a note when relaxed)
- **Exports:** JSON (structured), CSV (1 row per day)
- **Thin UI:** generate → auto‑pick → export (no map yet)

---

## Repository Layout (high level)

```
CityRoute/
├─ backend/
│  ├─ app.py                 # FastAPI endpoints
│  ├─ services/              # planner, clusterer, router, hotel_ranker, restaurants
│  ├─ storage/               # in‑memory stores
│  ├─ utils/                 # geo/time helpers
│  └─ data/                  # seed CSVs (POIs, Hotels, Restaurants)
├─ frontend/
│  ├─ src/
│  │  ├─ App.jsx             # thin demo UI
│  │  ├─ api.js              # axios calls
│  │  └─ main.jsx, index.css
│  └─ .env.example           # VITE_API_URL=http://127.0.0.1:8000
└─ docs/ (optional)          # SRS, diagrams, test plan, slides
```

---

## Running v1 (Local)

### 1) Backend

```bash
cd backend
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell:
# .venv\\Scripts\\Activate.ps1

pip install -r requirements.txt  # or: pip install fastapi uvicorn numpy scikit-learn pydantic
uvicorn app:app --reload         # runs at http://127.0.0.1:8000
```

> Swagger UI: `http://127.0.0.1:8000/docs`

### 2) Frontend

```bash
cd frontend
npm install
# Set backend URL (if not present):
cp .env.example .env    # contains VITE_API_URL=http://127.0.0.1:8000
npm run dev             # opens http://localhost:5173
```

---

## Quick API Test (CLI)

```bash
# Generate itinerary (uses seed CSVs)
curl -s -X POST http://127.0.0.1:8000/itinerary/generate \
  -H "Content-Type: application/json" \
  -d '{"city":"Pittsburgh","prefs":{"days":3,"travel_mode":"drive","detour_limit_minutes":15}}'

# Auto-pick meals (optional detour override)
curl -s -X POST http://127.0.0.1:8000/restaurants/auto_pick \
  -H "Content-Type: application/json" \
  -d '{"itinerary_id":"it-001","detour_limit_min":25}'
```

---

## Using the Frontend (Demo)

1. Open the app (Vite) at `http://localhost:5173`.
2. Fill **City**, **Days**, optional **Diet tags** (e.g., `vegetarian|vegan`), **Price** (`$`, `$$`, `$$$`), and **Detour limit** (min).
3. Click **Generate** → shows itinerary id, hotel id, day ids.
4. Click **Auto‑Pick Meals** → each day shows visits + lunch/dinner.
5. Click **Export JSON** / **Export CSV** to download files.

> If the backend restarts, in‑memory data resets—just click **Generate** again.

---

## Business Rules (v1)

- Days ∈ **[3, 7]**
- ≤ **40** POIs per itinerary
- Daily time budget ≈ **7h** (soft goal shown via totals)
- Meal windows: Lunch **11:30–14:00**, Dinner **17:30–20:30**
- Detour limit default **15 min** (UI lets you try other values)
- Diet/Price filters enforced when provided
- **No restaurant repeats** across days unless no open alternatives (adds note)
- API returns **IDs‑only** (consistent with SRS & diagrams)

---

## Seeds (CSV Expectations)

- `pois.csv`: `id,name,lat,lon,rating,review_count,must_go`
- `hotels.csv`: `id,name,lat,lon,rating,review_count,price_level`
- `restaurants.csv`: `id,name,lat,lon,rating,review_count,price_level,diet_tags,open_lunch,open_dinner`

**Coordinate sanity:** Pittsburgh is roughly `lat ~ 40.30–40.60`, `lon ~ -80.10 .. -79.80` (note the minus).

---

## Troubleshooting

- **CORS / network error in frontend** → backend must run at `http://127.0.0.1:8000`; check `.env`.
- **404 Itinerary not found** → backend restarted; generate a new itinerary.
- **Huge detour notes** → increase detour limit or fix restaurant coordinates; optional radius prefilter planned for v2.
- **CSV export** returns text field `csv_text`; the frontend downloads it as a file.

---

## What’s Next (v2 Ideas)

- Filters: **Only must‑go**, **Max POIs total**
- Show **names** alongside IDs (id→name lookup)
- Restaurant **radius prefilter** around day centroid
- Leaflet map overlay
- Optional DB (Postgres/PostGIS)

---

## License / Contact

- Course project — educational use.
- Contact: _Your Name_ · _Your Email_

