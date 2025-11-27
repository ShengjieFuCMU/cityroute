# CityRoute – Applied Project Submission

## Open these first
1. **docs/SRS.pdf** – Final Software Requirements Specification (with UML diagrams)
2. **docs/Day5_Traceability_TestPlan.pdf** – Traceability matrix & acceptance tests

## Folder map
docs/
SRS.pdf
Traceability_TestPlan.pdf
examples/
generate_request.json
itinerary_example.json
dayplan_example.json
diagrams/
usecase-cityroute.svg
class-cityroute.svg
seq-generate.svg
seq-autopick.svg
seq-regenerate.svg
data/
seeds/
pois.csv
hotels.csv
restaurants.csv
sources/ 
SRS.md
Day2_UseCases.md
Traceability_TestPlan.md
puml/
usecase-cityroute.puml
class-cityroute.puml
seq-generate.puml
seq-autopick.puml
seq-regenerate.puml

## Scope (first version)
- **City:** Pittsburgh
- **Trip length:** 3–7 days
- **POIs:** ≤ 40
- **Hotels/Restaurants:** curated small lists
- **Plan time:** under 10 seconds on a laptop

## Notes
- Itinerary uses **IDs everywhere** (Option B). See `docs/examples/itinerary_example.json` and `docs/examples/dayplan_example.json`.
- Default rules (also in SRS §7): daily time budget **7h**, detour limit **15min (default)**, minimum hotel rating **4.0** (fallback 3.5), meals **not required** unless the toggle is ON.

## Contact
- Name: Shengjie Fu
- Email: HU

