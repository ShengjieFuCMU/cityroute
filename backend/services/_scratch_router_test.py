# backend/services/_scratch_router_test.py
from services.router import route_day

# Synthetic cluster (roughly around two links)
pois = [
    {"id":"p1","name":"A","lat":40.4410,"lon":-80.0000},
    {"id":"p2","name":"B","lat":40.4420,"lon":-80.0020},
    {"id":"p3","name":"C","lat":40.4460,"lon":-79.9950},
    {"id":"p4","name":"D","lat":40.4445,"lon":-79.9975},
    {"id":"p5","name":"E","lat":40.4470,"lon":-79.9920},
]

# Approximate centroid for this day
centroid = (40.444, -79.998)

ids, minutes, dist_km = route_day(pois, centroid=centroid, city_speed_kmh=32.0)
print("ORDER:", ids)
print(f"TIME (min): {minutes:.1f}, DIST (km): {dist_km:.2f}")

# basic checks
assert set(ids) == set([p["id"] for p in pois]), "All POIs must be in the route"
assert 0.0 < dist_km < 20.0, "Distance out of expected range"
assert 0.0 < minutes < 60.0, "Time out of expected range"

# With a fixed start lock
ids2, minutes2, dist_km2 = route_day(pois, centroid=None, start_id="p3", city_speed_kmh=32.0)
assert ids2[0] == "p3", "Start lock must be honored"

print("All good ✅")

