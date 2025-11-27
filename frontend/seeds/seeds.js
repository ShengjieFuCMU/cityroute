// Load once at module import
import pois from '../../seeds/pois.json';
import hotels from '../../seeds/hotels.json';
import restaurants from '../../seeds/restaurants.json';

// Convert to { [id]: name }
export const poiName = Object.fromEntries(
  (pois || []).map(p => [String(p.id), p.name ?? undefined])
);

export const hotelName = Object.fromEntries(
  (hotels || []).map(h => [String(h.id), h.name ?? undefined])
);

export const restName = Object.fromEntries(
  (restaurants || []).map(r => [String(r.id), r.name ?? undefined])
);

