from storage.memory import itineraries, days, next_itinerary_id, next_day_id, snapshot_counts, reset_all

reset_all()
print("COUNTS (start):", snapshot_counts())
assert snapshot_counts() == (0, 0)

# Create IDs
it_id = next_itinerary_id()
d1 = next_day_id()
d2 = next_day_id()
print("IDS:", it_id, d1, d2)
assert it_id == "it-001" and d1 == "day1" and d2 == "day2"

# Write sample objects
itineraries[it_id] = {"id": it_id, "city": "Pittsburgh", "prefs": {"days": 2}, "day_ids": [d1, d2], "hotel_id": None, "warnings": []}
days[d1] = {"id": d1, "visit_ids": ["p1","p2"], "lunch_id": None, "dinner_id": None, "total_time_minutes": 180.0}
days[d2] = {"id": d2, "visit_ids": ["p3"], "lunch_id": "r1", "dinner_id": None, "total_time_minutes": 60.0}

print("COUNTS (after write):", snapshot_counts())
assert snapshot_counts() == (1, 2)

# Read back & verify
assert itineraries[it_id]["day_ids"] == ["day1","day2"]
assert days["day1"]["visit_ids"] == ["p1","p2"]
assert days["day2"]["lunch_id"] == "r1"

# Reset and re-check
reset_all()
print("COUNTS (after reset):", snapshot_counts())
assert snapshot_counts() == (0, 0)

print("All good ✅")

