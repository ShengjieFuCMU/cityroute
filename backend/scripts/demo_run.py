# backend/scripts/demo_run.py
from __future__ import annotations
import os
import json
import time
import pathlib
from typing import Dict, Any, List

import httpx  # already in requirements

DEFAULT_BASE = os.getenv("DEMO_BASE_URL", "http://127.0.0.1:8000")

SCENARIOS: List[Dict[str, Any]] = [
    # S1: default 2-day, loose prefs
    {"name": "s1_two_day_default", "payload": {"city": "Pittsburgh", "prefs": {"days": 2}}},
    # S2: only must-go + cap
    {"name": "s2_must_go_cap", "payload": {"city": "Pittsburgh", "prefs": {"days": 2, "only_must_go": True, "max_pois_total": 12}}},
    # S3: restaurant radius demo
    {"name": "s3_radius_demo", "payload": {"city": "Pittsburgh", "prefs": {"days": 1, "restaurant_radius_km": 0.5}}},
    # S4: 3-day with detour limit tweak
    {"name": "s4_three_day_detour", "payload": {"city": "Pittsburgh", "prefs": {"days": 3, "detour_limit_minutes": 12}}},
]

def run_scenario(client: httpx.Client, base: str, sc: Dict[str, Any], outdir: pathlib.Path) -> None:
    name = sc["name"]
    payload = sc["payload"]

    # 1) generate
    r = client.post(f"{base}/itinerary/generate", json=payload, timeout=60)
    r.raise_for_status()
    gen = r.json()
    itid = gen["itinerary_id"]

    # 2) autopick meals
    r2 = client.post(f"{base}/restaurants/auto_pick", json={"itinerary_id": itid}, timeout=60)
    r2.raise_for_status()
    meals = r2.json()

    # 3) export json
    rj = client.post(f"{base}/export", json={"itinerary_id": itid, "format": "json"}, timeout=60)
    rj.raise_for_status()
    exp_json = rj.json()

    # 4) export csv2
    rc = client.post(f"{base}/export", json={"itinerary_id": itid, "format": "csv2"}, timeout=60)
    rc.raise_for_status()
    exp_csv2 = rc.json()

    # write files
    sc_dir = outdir / name
    sc_dir.mkdir(parents=True, exist_ok=True)

    (sc_dir / "generate.json").write_text(json.dumps(gen, indent=2))
    (sc_dir / "meals.json").write_text(json.dumps(meals, indent=2))
    (sc_dir / "export.json").write_text(json.dumps(exp_json, indent=2))
    (sc_dir / exp_csv2["filename"]).write_text(exp_csv2["csv_text"])

    print(f"[demo] wrote {name} -> {sc_dir}")

def main() -> None:
    base = DEFAULT_BASE
    ts = time.strftime("%Y%m%d_%H%M%S")
    outdir = pathlib.Path(__file__).resolve().parents[1] / "demo" / ts
    outdir.mkdir(parents=True, exist_ok=True)

    # Tip: ensure your FastAPI is running: `uvicorn app:app --reload`
    with httpx.Client(timeout=60) as client:
        for sc in SCENARIOS:
            run_scenario(client, base, sc, outdir)
    print(f"[demo] all scenarios saved under {outdir}")

if __name__ == "__main__":
    main()

