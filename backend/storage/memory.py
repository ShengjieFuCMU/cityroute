# backend/storage/memory.py
from __future__ import annotations
from typing import Dict, Any, Tuple

# In-memory stores for the midterm demo (not persistent)
itineraries: Dict[str, Dict[str, Any]] = {}
days: Dict[str, Dict[str, Any]] = {}

# Monotonic, human-readable IDs
_counters = {"it": 0, "day": 0}

def next_itinerary_id() -> str:
    _counters["it"] += 1
    return f"it-{_counters['it']:03d}"

def next_day_id() -> str:
    _counters["day"] += 1
    return f"day{_counters['day']}"

# --- optional utilities that help during testing ---

def snapshot_counts() -> Tuple[int, int]:
    """Return (#itineraries, #days) for quick sanity checks."""
    return (len(itineraries), len(days))

def reset_all() -> None:
    """Clear all in-memory data and reset counters. Handy for repeated scratch tests."""
    itineraries.clear()
    days.clear()
    _counters["it"] = 0
    _counters["day"] = 0

