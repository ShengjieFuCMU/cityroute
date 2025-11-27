# backend/services/_scratch_planner_test.py
from services.planner import generate, autopick_meals, regenerate_with_locks
from storage.memory import itineraries, days

# --- seed (small demo) ---
pois = [
    {"id":"p1","name":"A","lat":40.4410,"lon":-80.0000,"rating":4.5,"review_count":100,"must_go":True},
    {"id":"p2","name":"B","lat":40.4420,"lon":-80.0020,"rating":4.2,"review_count":80,"must_go":False},
    {"id":"p3","name":"C","lat":40.4460,"lon":-79.9950,"rating":4.1,"review_count":50,"must_go":False},
    {"id":"p4","name":"D","lat":40.4550,"lon":-79.9500,"rating":4.6,"review_count":200,"must_go":False},
    {"id":"p5","name":"E","lat":40.4560,"lon":-79.9510,"rating":4.3,"review_count":120,"must_go":False},
    {"id":"p6","name":"F","lat":40.4710,"lon":-79.9310,"rating":4.8,"review_count":500,"must_go":True},
]

hotels = [
    {"id":"h1","name":"Hotel A","lat":40.445,"lon":-79.998,"rating":4.6,"review_count":400,"price_level":"$$"},
    {"id":"h2","name":"Hotel B","lat":40.468,"lon":-79.935,"rating":4.1,"review_count":120,"price_level":"$$"},
    {"id":"h3","name":"Hotel C","lat":40.460,"lon":-79.960,"rating":4.8,"review_count":80,"price_level":"$$$"},
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

prefs = {"days": 3, "travel_mode": "drive", "detour_limit_minutes": 15, "price_range": "$$", "diet_tags": ["vegetarian"]}

# --- Generate ---
res = generate("Pittsburgh", prefs, pois, hotels, restaurants, locks=[])
print("GENERATE:", res)
itid = res["itinerary_id"]

# Validate days stored
for did in res["day_ids"]:
    print("DAY:", did, days[did])

# --- Auto-pick meals ---
meals = autopick_meals(itid)
print("MEALS:", meals)
assert len(meals["days"]) == len(res["day_ids"])

# --- Regenerate with a locked hotel ---
regen = regenerate_with_locks(itid, locks=[{"type": "hotel", "id": "h2"}])
print("REGENERATE:", regen)
assert regen["hotel_id"] == "h2"

print("All good ✅")

