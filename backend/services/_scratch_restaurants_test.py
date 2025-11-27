from services.restaurants import autopick_for_day

route_pts = [
    (40.4431, -79.9496),
    (40.4448, -79.9483),
    (40.4472, -79.9460),
    (40.4522, -79.9421),
    (40.4570, -79.9390)
]

restaurants = [
    {"id":"r1","name":"Veggie Corner","lat":40.4460,"lon":-79.9465,"rating":4.6,"review_count":200,
     "price_level":"$$","diet_tags":"vegetarian|vegan","open_lunch":"11:30-14:00","open_dinner":"17:30-20:30"},
    {"id":"r2","name":"Evening Eats","lat":40.4518,"lon":-79.9425,"rating":4.5,"review_count":120,
     "price_level":"$","diet_tags":"", "open_lunch":"10:00-11:00", "open_dinner":"17:30-20:00"},
    {"id":"r3","name":"Prime Table","lat":40.4590,"lon":-79.9360,"rating":4.8,"review_count":90,
     "price_level":"$$$","diet_tags":"vegetarian", "open_lunch":"11:30-14:00","open_dinner":"17:30-21:00"},
    {"id":"r4","name":"Far Grill","lat":40.4700,"lon":-79.9300,"rating":4.2,"review_count":60,
     "price_level":"$$","diet_tags":"", "open_lunch":"11:30-14:00","open_dinner":"17:30-20:30"},
]

prefs = {"diet_tags":["vegetarian"], "price_range":"$$"}

# First day picks (no-repeat set starts empty)
used = set()
l1, d1, notes1 = autopick_for_day(route_pts, restaurants, prefs=prefs, used_ids=used)
print("DAY1 LUNCH:", l1, "DINNER:", d1, "NOTES:", notes1)
assert l1 is not None and d1 is not None

# Second day with the same route & prefs — should avoid r1/r3 if already used
l2, d2, notes2 = autopick_for_day(route_pts, restaurants, prefs=prefs, used_ids=used)
print("DAY2 LUNCH:", l2, "DINNER:", d2, "NOTES:", notes2)

# No duplicates across both days unless unavoidable
chosen_all = [x for x in [l1, d1, l2, d2] if x]
assert len(chosen_all) == len(set(chosen_all)) or "Relaxed filters and allowed repeats" in " ".join(notes1 + notes2)

print("All good ✅")

