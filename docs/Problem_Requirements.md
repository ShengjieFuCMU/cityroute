# CityRoute — Day 1: Problem & Requirements
_Last updated: 2025-09-15_

> **Scope (first version):** Pittsburgh only · 3–7 days · ≤40 POIs · curated hotels/restaurants · plan <10s

## Problem Statement
Planning a short city trip is tedious—people juggle maps, blogs, and reviews, then still struggle to split days, pick a hotel, and choose meals. **CityRoute** turns a user’s list of places into a clear **3–7-day** plan for **Pittsburgh**, orders each day to reduce travel time, and suggests a convenient hotel plus lunch and dinner. The first version is intentionally small: **≤40 points of interest**, a **small curated list** of hotels and restaurants, and fast, simple methods that generate a plan in **under 10 seconds** on a laptop. Users can lock favorites and regenerate.

## Functional Requirements (FR)
- **FR1** Add POIs on the map/search; tag **must-go / nice-to-go**.
- **FR2** Set trip length (**3–7 days**) & travel mode; group nearby places by day.
- **FR3** Order visits within each day; show estimated/total time.
- **FR4** Suggest hotels ranked by convenience (distance/time + rating).
- **FR5** Restaurants per day: **manual pick** with filters (cuisine/price/diet/open-now).
- **FR6** **Auto-Pick** lunch/dinner (respect open hours, detour limit, rating/price/diet).
- **FR7** **Lock** any POI/hotel/restaurant and **Regenerate** around locks.
- **FR8** **Export** itinerary (PDF/CSV/JSON).
- **FR9 (optional)** Sign-in to save itineraries.

## Non-Functional Requirements (NFR)
- **NFR1 Performance**: ≤40 POIs planned in **<10s** on a laptop.
- **NFR2 Usability**: simple UI; clear warnings (e.g., must-go overload).
- **NFR3 Security/Privacy**: no unnecessary personal data; protect saved plans if login exists.
- **NFR4 Reliability**: graceful fallbacks (closed restaurant → next best open within detour).
- **NFR5 Portability**: modern desktop browsers.

