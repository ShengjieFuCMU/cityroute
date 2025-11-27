# backend/app.py
from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
import os, io, csv, json

from functools import lru_cache

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.planner import generate as plan_generate, autopick_meals, regenerate_with_locks
from storage.memory import itineraries, days

# -----------------------------------------------------------------------------
# FastAPI setup
# -----------------------------------------------------------------------------
app = FastAPI(title="CityRoute API", version="0.3.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # dev-friendly; lock down for prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Seed loading (robust to encoding and delimiter)
# -----------------------------------------------------------------------------
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def _read_csv(path: str) -> List[Dict[str, Any]]:
    """
    Read a CSV file into a list of dicts.
    - Tries encodings: utf-8, utf-8-sig, cp1252, latin-1
    - Sniffs delimiter: comma or semicolon
    """
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    with open(path, "rb") as fb:
        raw = fb.read()

    text = None
    last_err = None
    for enc in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError as e:
            last_err = e
    if text is None:
        raise ValueError(f"Could not decode {path} as UTF-8/CP1252/Latin-1: {last_err}")

    sio = io.StringIO(text)
    sample = sio.read(4096)
    sio.seek(0)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;")
    except csv.Error:
        dialect = csv.excel  # default comma

    reader = csv.DictReader(sio, dialect=dialect)
    rows = [row for row in reader]
    if not rows:
        raise ValueError(f"{path} appears to be empty or has no rows.")
    return rows

def _normalize_pois(pois: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for p in pois:
        p["lat"] = float(p["lat"])
        p["lon"] = float(p["lon"])
        p["rating"] = float(p.get("rating", 0) or 0)
        p["review_count"] = int(p.get("review_count", 0) or 0)
        p["must_go"] = str(p.get("must_go", "")).strip().lower() in ("true", "1", "yes", "y")
    return pois

def _normalize_hotels(hotels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for h in hotels:
        h["lat"] = float(h["lat"])
        h["lon"] = float(h["lon"])
        h["rating"] = float(h.get("rating", 0) or 0)
        h["review_count"] = int(h.get("review_count", 0) or 0)
    return hotels

def _normalize_restaurants(restaurants: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for r in restaurants:
        r["lat"] = float(r["lat"])
        r["lon"] = float(r["lon"])
        r["rating"] = float(r.get("rating", 0) or 0)
        r["review_count"] = int(r.get("review_count", 0) or 0)
    return restaurants

def load_seeds_if_missing(
    pois: Optional[List[Dict[str, Any]]],
    hotels: Optional[List[Dict[str, Any]]],
    restaurants: Optional[List[Dict[str, Any]]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    if pois is None:
        pois = _normalize_pois(_read_csv(os.path.join(DATA_DIR, "pois.csv")))
    else:
        pois = _normalize_pois(pois)

    if hotels is None:
        hotels = _normalize_hotels(_read_csv(os.path.join(DATA_DIR, "hotels.csv")))
    else:
        hotels = _normalize_hotels(hotels)

    if restaurants is None:
        restaurants = _normalize_restaurants(_read_csv(os.path.join(DATA_DIR, "restaurants.csv")))
    else:
        restaurants = _normalize_restaurants(restaurants)

    return pois, hotels, restaurants

# ---- small in-process cache for seed tables (read-only) ----
@lru_cache(maxsize=1)
def _seed_tables_cached() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    return load_seeds_if_missing(None, None, None)

def _index_by_id(rows: List[Dict[str, Any]]) -> Dict[str, Optional[str]]:
    # map id -> name (name may be None)
    out: Dict[str, Optional[str]] = {}
    for r in rows:
        rid = str(r.get("id"))
        nm = r.get("name")
        out[rid] = nm if (nm is not None and str(nm) != "") else None
    return out

# -----------------------------------------------------------------------------
# Pydantic schemas
# -----------------------------------------------------------------------------
class Lock(BaseModel):
    type: str   # "poi" | "hotel" | "restaurant"
    id: str

class GenerateReq(BaseModel):
    city: str = "Pittsburgh"
    prefs: Dict[str, Any] = {"days": 3, "travel_mode": "drive", "detour_limit_minutes": 15}
    pois: Optional[List[Dict[str, Any]]] = None
    hotels: Optional[List[Dict[str, Any]]] = None
    restaurants: Optional[List[Dict[str, Any]]] = None
    locks: Optional[List[Lock]] = None

class GenerateResp(BaseModel):
    itinerary_id: str
    day_ids: List[str]
    hotel_id: Optional[str] = None
    warnings: List[str] = []

class AutoPickReq(BaseModel):
    itinerary_id: str
    day_ids: Optional[List[str]] = None
    detour_limit_min: float = 15.0

class DaysWithMeals(BaseModel):
    id: str
    lunch_id: Optional[str] = None
    dinner_id: Optional[str] = None
    notes: List[str] = []

class AutoPickResp(BaseModel):
    days: List[DaysWithMeals]

class ExportReq(BaseModel):
    itinerary_id: str
    # accepts: "json" | "csv" | "csv2"
    format: str = "json"

# Lookup response models
class LookupItem(BaseModel):
    id: str
    name: Optional[str] = None

class LookupResp(BaseModel):
    items: List[LookupItem]

# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@app.post("/itinerary/generate", response_model=GenerateResp)
def api_generate(req: GenerateReq):
    try:
        pois, hotels, restaurants = load_seeds_if_missing(req.pois, req.hotels, req.restaurants)

        # light request sanity (friendly 4xxs)
        days_val = int(req.prefs.get("days", 3))
        if days_val <= 0:
            raise ValueError("days must be a positive integer")

        res = plan_generate(
            req.city,
            req.prefs,
            pois,
            hotels,
            restaurants,
            locks=[l.dict() for l in (req.locks or [])],
        )
        return res
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=f"Seed file not found: {e}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Surface a readable error for easier debugging during the midterm/final
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")

@app.post("/restaurants/auto_pick", response_model=AutoPickResp)
def api_auto_pick(req: AutoPickReq):
    if req.itinerary_id not in itineraries:
        raise HTTPException(status_code=404, detail="Itinerary not found")
    res = autopick_meals(req.itinerary_id, day_ids=req.day_ids, detour_limit_min=req.detour_limit_min)
    return res

@app.get("/itineraries/{itinerary_id}")
def api_get_itinerary(itinerary_id: str):
    it = itineraries.get(itinerary_id)
    if not it:
        raise HTTPException(status_code=404, detail="Itinerary not found")
    # IDs-only view (matches SRS)
    return {
        "id": it["id"],
        "city": it["city"],
        "prefs": it["prefs"],
        "day_ids": it["day_ids"],
        "hotel_id": it["hotel_id"],
        "warnings": it["warnings"],
    }

@app.get("/days/{day_id}")
def api_get_day(day_id: str):
    d = days.get(day_id)
    if not d:
        raise HTTPException(status_code=404, detail="Day not found")
    return d

@app.post("/export")
def api_export(req: ExportReq):
    it = itineraries.get(req.itinerary_id)
    if not it:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    # Materialize itinerary + days
    packed = {
        "itinerary_id": it["id"],
        "city": it["city"],
        "hotel_id": it["hotel_id"],
        "prefs": it["prefs"],
        "warnings": it["warnings"],
        "days": [days[did] for did in it["day_ids"] if did in days],
    }

    fmt = (req.format or "json").lower()
    if fmt == "json":
        return packed

    if fmt == "csv":
        # One CSV: day_id, visit_ids (pipe-joined), lunch_id, dinner_id, total_time_minutes
        buff = io.StringIO()
        writer = csv.writer(buff)
        writer.writerow(["day_id", "visit_ids", "lunch_id", "dinner_id", "total_time_minutes"])
        for d in packed["days"]:
            writer.writerow([
                d["id"],
                "|".join(d["visit_ids"]),
                d.get("lunch_id") or "",
                d.get("dinner_id") or "",
                d["total_time_minutes"],
            ])
        csv_text = buff.getvalue()
        # Return CSV as text field (simple for midterm/final; front-end can save)
        return {
            "filename": f"{it['id']}_days.csv",
            "content_type": "text/csv",
            "csv_text": csv_text
        }

    if fmt == "csv2":
        """
        Richer, row-per-stop CSV (IDs only).
        Columns:
          itinerary_id, day_id, order, stop_type{poi|lunch|dinner|hotel}, stop_id,
          arrival_min, depart_min, planned_minutes, notes
        - arrival/depart may be blank (no duration model yet).
        - order is a simple integer walk through the day's sequence:
            POIs first (1..N), then lunch (N+1 if present), then dinner (N+2 if present).
        - A single optional hotel row is included once (empty day_id, blank order).
        """
        buff = io.StringIO()
        writer = csv.writer(buff)
        header = [
            "itinerary_id", "day_id", "order", "stop_type", "stop_id",
            "arrival_min", "depart_min", "planned_minutes", "notes"
        ]
        writer.writerow(header)

        itid = it["id"]

        # Optional hotel row (itinerary-level)
        if it.get("hotel_id"):
            writer.writerow([itid, "", "", "hotel", it["hotel_id"], "", "", "", ""])

        # Per-day rows
        for d in packed["days"]:
            day_id = d["id"]
            visits: List[str] = list(d.get("visit_ids") or [])
            # POIs in routed order
            for idx, pid in enumerate(visits, 1):
                writer.writerow([itid, day_id, idx, "poi", pid, "", "", "", ""])

            # Meals appended after visits using continuing order index
            next_ord = len(visits) + 1
            if d.get("lunch_id"):
                writer.writerow([itid, day_id, next_ord, "lunch", d["lunch_id"], "", "", "", ""])
                next_ord += 1
            if d.get("dinner_id"):
                writer.writerow([itid, day_id, next_ord, "dinner", d["dinner_id"], "", "", "", ""])

        csv_text = buff.getvalue()
        return {
            "filename": f"{it['id']}_stops.csv",
            "content_type": "text/csv",
            "csv_text": csv_text
        }

    raise HTTPException(status_code=400, detail="format must be 'json', 'csv', or 'csv2'")

# -----------------------------------------------------------------------------
# Phase 1: Name lookup endpoint (IDs -> names), read-only
# -----------------------------------------------------------------------------
@app.get("/lookup/{kind}", response_model=LookupResp)
def api_lookup(kind: str, ids: str = Query(..., description="Comma-separated IDs")):
    """
    Resolve names for a list of IDs without changing the IDs-only planning/export contract.
    kind: 'poi' | 'hotel' | 'restaurant'
    ids:  comma-separated list like 'poi1,poi3'
    """
    kind_lc = kind.strip().lower()
    if kind_lc not in ("poi", "hotel", "restaurant"):
        raise HTTPException(status_code=400, detail="kind must be poi|hotel|restaurant")

    id_list = [i.strip() for i in ids.split(",") if i.strip()]
    if not id_list:
        raise HTTPException(status_code=400, detail="ids must be a non-empty comma-separated string")

    pois, hotels, restaurants = _seed_tables_cached()
    table = pois if kind_lc == "poi" else (hotels if kind_lc == "hotel" else restaurants)
    index = _index_by_id(table)

    items = [{"id": i, "name": index.get(i)} for i in id_list]
    return {"items": items}

