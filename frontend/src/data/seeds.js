// frontend/src/data/seeds.js
// Build ID -> name maps from your JSON seed files.
// These imports are relative to THIS file (src/data/*)
// and expect JSON to live at frontend/seeds/*.json

import pois from '../../seeds/pois.json';
import hotels from '../../seeds/hotels.json';
import restaurants from '../../seeds/restaurants.json';

// Each JSON is expected to be an array of objects like: { "id": "poi5", "name": "National Aviary" }

export const poiName = Object.fromEntries(
  (Array.isArray(pois) ? pois : []).map(p => [String(p.id), p.name ?? undefined])
);

export const hotelName = Object.fromEntries(
  (Array.isArray(hotels) ? hotels : []).map(h => [String(h.id), h.name ?? undefined])
);

export const restName = Object.fromEntries(
  (Array.isArray(restaurants) ? restaurants : []).map(r => [String(r.id), r.name ?? undefined])
);

