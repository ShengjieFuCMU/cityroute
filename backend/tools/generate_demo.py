#!/usr/bin/env python3
import json, requests

BASE = "http://127.0.0.1:8000"

payload = {
  "city": "Pittsburgh",
  "prefs": {
    "days": 3,
    "travel_mode": "drive",
    "detour_limit_minutes": 15,
    "only_must_go": False,
    "max_pois_total": 40
  }
}

def main():
    # 1) Generate
    r = requests.post(f"{BASE}/itinerary/generate", json=payload, timeout=30)
    r.raise_for_status()
    gen = r.json()
    itid = gen["itinerary_id"]
    day_ids = gen.get("day_ids", [])
    print("Itinerary:", itid)
    print("Days:", ", ".join(day_ids))
    print("Hotel:", gen.get("hotel_id"))
    print("Warnings:", "; ".join(gen.get("warnings", [])))

    # 2) Auto-pick meals
    r = requests.post(f"{BASE}/restaurants/auto_pick",
                      json={"itinerary_id": itid}, timeout=30)
    r.raise_for_status()
    meals = r.json()

    # 3) Export JSON bundle (itinerary + days + meals)
    export_json = {
      "itinerary": requests.get(f"{BASE}/itineraries/{itid}", timeout=10).json(),
      "days": [requests.get(f"{BASE}/days/{d}", timeout=10).json() for d in day_ids],
      "meals": meals
    }
    with open("demo_export.json", "w") as f:
        f.write(json.dumps(export_json, indent=2))

    # 4) Export CSV (days)
    r = requests.post(f"{BASE}/export",
                      json={"itinerary_id": itid, "format": "csv"}, timeout=30)
    r.raise_for_status()
    with open("demo_days.csv", "w") as f:
        f.write(r.json()["csv_text"])

    # 5) Export CSV2 (row-per-stop)
    r = requests.post(f"{BASE}/export",
                      json={"itinerary_id": itid, "format": "csv2"}, timeout=30)
    r.raise_for_status()
    with open("demo_stops.csv", "w") as f:
        f.write(r.json()["csv_text"])

if __name__ == "__main__":
    main()

