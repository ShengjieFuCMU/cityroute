# Day2_UseCases.md

## Use Case Index

| UC ID | Title                       | Goal (one line)                                      |
|------:|-----------------------------|------------------------------------------------------|
| UC1   | Generate Itinerary          | Make a 3–7 day plan from user-selected places       |
| UC2   | Choose Hotel                | Pick a convenient hotel from a ranked list          |
| UC3   | Restaurants — Manual        | User selects lunch/dinner with simple filters       |
| UC4   | Restaurants — Auto-Pick     | System selects lunch/dinner that fit the plan       |
| UC5   | Lock & Regenerate           | Keep favorites and remake the plan around them      |
| UC6   | Export Plan                 | Download the plan as PDF/CSV/JSON                   |


---

## UC1 — Generate Itinerary

**Primary Actor:** Traveler (user)  
**Scope:** CityRoute (first version, Pittsburgh only)  
**Level:** User goal  

**Stakeholders & Interests**  
- **Traveler:** Wants a simple, realistic plan quickly.  
- **System:** Must respect limits (days 3–7, POIs ≤ 40) and produce a plan under 10 seconds.

**Preconditions**  
- City is **Pittsburgh**.  
- Traveler has added **1–40 POIs** (points of interest).  
- Traveler has chosen **3–7 days** and a travel mode (Walk/Drive).

**Trigger**  
- Traveler clicks **Generate**.

**Main Flow**  
1. System validates inputs (days in range, POIs ≤ 40).  
2. System **groups nearby POIs by day** (k = chosen days).  
3. System **orders visits** inside each day (nearest-neighbor start, then 2-opt improve).  
4. System **estimates times** (per stop, per day, and total) using the chosen mode.  
5. System shows **Day 1..Day k** cards with ordered visits and times.  
6. Traveler reviews the plan.

**Alternate Flows**  
3a. *(Alternative to Step 3)* If **locks** from an earlier run exist, the system keeps the locked items and routes around them.

**Exception Flows**  
2e. *(At Step 2)* If **must-go density** makes any day exceed the daily time budget, the system shows a message and suggests increasing days or unchecking some POIs.  
4e. *(At Step 4)* If any POI has invalid coordinates, the system flags it and asks the traveler to fix or remove it.

**Postconditions (Success)**  
- A k-day plan is displayed with ordered visits and time estimates.

**Postconditions (Failure)**  
- Traveler sees a clear message with what to change (e.g., reduce must-go items or add a day).

**Related FRs**  
- FR1, FR2, FR3

**Validation Rules touched**  
- Days ∈ [3..7]; POIs ≤ 40; valid coordinates; daily time budget respected; plan < 10 seconds.


---

## UC2 — Choose Hotel

**Primary Actor:** Traveler  
**Scope:** CityRoute (first version, Pittsburgh only)  
**Level:** User goal  

**Preconditions**  
- A plan from **UC1** exists (Day 1..k shown).

**Trigger**  
- Traveler opens **Hotel suggestions** for the current plan.

**Main Flow**  
1. System computes each day’s **centroid** and ranks hotels by: short distance to centroids, rating, review count.  
2. System shows a **short list** (for example, top 5).  
3. Traveler selects a hotel.  
4. System updates **travel/time estimates** and marks the hotel on the map.

**Alternate Flows**  
2a. Traveler applies **filters** (price, minimum rating) → list updates.  
3a. Traveler **previews** the hotel on the map → returns to list.

**Exception Flows**  
2e. No hotel meets the filters → system shows the **best available** and explains why.

**Postconditions (Success)**  
- The selected hotel is attached to the plan and visible on the map.

**Related FRs**  
- FR4

**Validation Rules touched**  
- Hotel ranking formula; filter ranges; map marker placement.


---

## UC3 — Restaurants — Manual

**Primary Actor:** Traveler  
**Scope:** CityRoute (first version, Pittsburgh only)  
**Level:** User goal  

**Preconditions**  
- A plan from **UC1** exists.  
- Day X is selected for meal planning.

**Trigger**  
- Traveler opens **Lunch** (or **Dinner**) for Day X.

**Main Flow**  
1. Traveler sets filters: **cuisine**, **price**, **diet** (e.g., vegetarian), **open-now**.  
2. System lists restaurants near Day X area, respecting **detour limit** and filters.  
3. Traveler selects a restaurant.  
4. System updates **Day X timing** and shows the pick on the map.

**Exception Flows**  
2e. No restaurant matches filters → system suggests the **closest open** option within the detour limit and explains.

**Postconditions (Success)**  
- Lunch/Dinner is set for Day X and shown on the map.

**Related FRs**  
- FR5

**Validation Rules touched**  
- Restaurant open hours; detour ≤ limit; filters applied.


---

## UC4 — Restaurants — Auto-Pick

**Primary Actor:** Traveler  
**Scope:** CityRoute (first version, Pittsburgh only)  
**Level:** User goal  

**Preconditions**  
- A plan from **UC1** exists.

**Trigger**  
- Traveler toggles **Auto-Pick** for meals and saves.

**Main Flow**  
1. System identifies **lunch (11:30–14:00)** and **dinner (17:30–20:30)** windows for each day.  
2. System scores restaurants by: **rating**, **review count**, **diet/price** match, **open hours**, **detour**, and **diversity** (avoid same cuisine day-after-day).  
3. System chooses a restaurant for lunch and dinner per day.  
4. Traveler reviews the picks and can tap **Swap** to change a choice.

**Alternate Flows**  
4a. Traveler taps **Swap** → system shows the **next best** candidate.

**Exception Flows**  
2e. No candidate within time/detour window → system explains and proposes the **closest feasible** fallback.

**Postconditions (Success)**  
- Lunch and dinner are set for each day; traveler can still override manually.

**Related FRs**  
- FR6, FR7

**Validation Rules touched**  
- Meal time windows; detour ≤ limit; diet/price filters; diversity rule.


---

## UC5 — Lock & Regenerate

**Primary Actor:** Traveler  
**Scope:** CityRoute (first version, Pittsburgh only)  
**Level:** User goal  

**Preconditions**  
- A plan exists from **UC1**.  
- Traveler has chosen one or more **locks** (POI, hotel, or restaurant).

**Trigger**  
- Traveler clicks **Regenerate**.

**Main Flow**  
1. System records the **locks**.  
2. System re-groups and re-routes **around locks**.  
3. System updates times and shows the refreshed plan.

**Exception Flows**  
2e. Locks make a valid plan impossible (exceeds daily time budget) → system shows the **conflict** and suggests removing some locks or adding a day.

**Postconditions (Success)**  
- A new plan is shown that **preserves all locked items**.

**Related FRs**  
- FR7

**Validation Rules touched**  
- Locks are immutable in the new plan; conflict messages when constraints fail.


---

## UC6 — Export Plan

**Primary Actor:** Traveler  
**Scope:** CityRoute (first version, Pittsburgh only)  
**Level:** User goal  

**Preconditions**  
- A plan exists from **UC1**.

**Trigger**  
- Traveler clicks **Export** and chooses **PDF**, **CSV**, or **JSON**.

**Main Flow**  
1. System validates the plan (for example, if traveler required meals, check that lunch/dinner exist for each day).  
2. System generates the selected **file**.  
3. Traveler downloads the file.

**Exception Flows**  
1e. Validation fails → system shows what is missing and how to fix it (e.g., “Add lunch for Day 2 or turn off ‘Meals required’.”)

**Postconditions (Success)**  
- File is downloaded with ordered POIs, hotel, meals, and times.

**Related FRs**  
- FR8

**Validation Rules touched**  
- File schema; presence of required fields.


---

## Validation Rules (central list)

**Trip & Data**  
- **Days** must be **3–7**.  
- **Total POIs** must be **≤ 40**.  
- **Coordinates** must be valid numbers (lat in −90..90, lon in −180..180).

**Time & Budget**  
- **Daily time budget** (visiting + short moves) default = **7 hours** per day.  
- If estimated time for any day exceeds the budget → show message and suggest fixes.

**Meals**  
- **Lunch window**: **11:30–14:00**.  
- **Dinner window**: **17:30–20:30**.  
- **Detour limit** for restaurants: **≤ 15 minutes** added travel time (default).  
- **Diet/price filters** must be honored when set.  
- **Cuisine diversity**: avoid same cuisine on consecutive days when possible.

**Hotel**  
- **Convenience score** uses distance to day centroids + rating + review count.  
- **Minimum rating** default: **4.0** (adjustable).  
- If no hotel meets filters → show best available.

**Locking & Regeneration**  
- **Locked** POIs/hotel/restaurants must be **kept** in the new plan.  
- If locks cause a conflict (time budget blown) → show conflict and suggest removing some locks or adding days.

**Performance**  
- For **≤ 40 POIs**, generate a plan in **< 10 seconds** on a typical laptop.

**Privacy**  
- Do not store or export personal data beyond the plan itself.

---

## Coverage (FR ↔ UC)

| FR | Covered by Use Case(s) |
|---|---|
| **FR1** Add POIs & tags | UC1 |
| **FR2** Group by day | UC1 |
| **FR3** Order visits & show times | UC1 |
| **FR4** Hotel suggestion | UC2 |
| **FR5** Restaurants manual | UC3 |
| **FR6** Restaurants auto-pick | UC4 |
| **FR7** Lock & Regenerate | UC5 |
| **FR8** Export | UC6 |
| **FR9** (optional) Sign-in | *(not covered in Day 2; add later if needed)* |

---

## Open Questions (to confirm later)

1. **Daily time budget** default is set to **7 hours** — keep or adjust?  
2. **Detour limit** default **15 minutes** — OK for both lunch and dinner?  
3. **Minimum hotel rating** default **4.0** — should we allow 3.5 if few options?  
4. **Meals required?** Do we require lunch/dinner every day, or allow skipping?  
5. **Walking vs Driving:** Do we need different average speeds or limits per mode?  
6. **Max POIs per day:** Add a soft cap (e.g., 12 per day) before warnings?


