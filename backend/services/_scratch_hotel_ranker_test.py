# backend/services/_scratch_hotel_ranker_test.py
from services.hotel_ranker import rank_hotels

# Day centroids (e.g., 3-day trip)
centroids = [
    (40.44, -80.00),
    (40.455, -79.95),
    (40.47, -79.93),
]

hotels = [
    {"id":"h1","name":"Hotel A","lat":40.445,"lon":-79.998,"rating":4.6,"review_count":400,"price_level":"$$"},
    {"id":"h2","name":"Hotel B","lat":40.468,"lon":-79.935,"rating":4.1,"review_count":120,"price_level":"$$"},
    {"id":"h3","name":"Hotel C","lat":40.460,"lon":-79.960,"rating":4.8,"review_count":80,"price_level":"$$$"},
    {"id":"h4","name":"Hotel D","lat":40.430,"lon":-80.020,"rating":3.9,"review_count":900,"price_level":"$"},  # low rating
    {"id":"h5","name":"Hotel E","lat":40.458,"lon":-79.950,"rating":4.0,"review_count":50,"price_level":"$$"},
]

# Default (min_rating=4.0, relax to 3.5 if too few)
ids, scored = rank_hotels(hotels, centroids, return_debug=True)
print("ORDER:", ids)
for r in scored[:3]:
    print(f"Top: {r['id']} rating={r['rating']} reviews={r['review_count']} avg_dist_km={r['avg_dist_km']:.2f} score={r['score']:.3f}")

# Basic checks
assert ids[0] in {"h1","h3"}, "A close, high-rated hotel should win"
assert "h4" not in ids[:3], "Low-rated hotel should be filtered unless needed"

# Tight filter test: if we set min_rating very high, ensure relax/fallback works
ids2 = rank_hotels(hotels, centroids, min_rating=4.9, relax_to=4.0)
assert len(ids2) >= 1, "Relaxation should allow candidates"

print("All good ✅")

