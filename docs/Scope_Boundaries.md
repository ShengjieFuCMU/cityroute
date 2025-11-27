# Scope & Boundaries (First Version)
## In Scope
- One city: **Pittsburgh**
- Trip length **3–7 days**, **≤40 POIs**
- Curated lists: **10–15 hotels**, **30–60 restaurants**
- Simple fast rules: group nearby places, quick route guess, meal picks respect open hours & short detours
- Export to PDF/CSV/JSON; lock & regenerate

## Not in Scope (for now)
- No new-place recommendations from deep review analysis or personal-interest modeling
- No automatic filtering of “unrealistic” POIs beyond basic time/detour checks
- No complex bus/train mixing or live traffic

## Assumptions & Constraints
- Seed data (CSV/JSON) available; no external API required to demo
- Desktop browser use; English UI to start
- Performance target: <10s on a typical laptop

