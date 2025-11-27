# Day 5 — Traceability & Test Plan (CityRoute)

## 1. Overview
This document links **requirements → use cases → SRS sections → tests**, and defines the acceptance **test plan** for the first version of CityRoute (single city: Pittsburgh; 3–7 days; ≤40 POIs; curated hotel/restaurant lists).

**Pre-Test Setup**
- City: Pittsburgh
- Seeds: ~20 POIs, 8 hotels, 20 restaurants
- Days: 3 (default)
- Travel mode: Drive
- Daily time budget: 7 hours/day
- Detour limit: 15 minutes (default)
- Lunch/Dinner windows: 11:30–14:00, 17:30–20:30
- Meals required: OFF by default (toggle can enforce)
- Browser: Chrome desktop


---

## 2. Traceability Matrix

### 2.1 Functional Coverage (FR ↔ UC ↔ SRS ↔ Test)
| FR ID | Requirement (short) | Use Case(s) | SRS Section | Test ID(s) |
|---|---|---|---|---|
| **FR1** | Add POIs & must-go tags | UC1 | §3.1 | TC1 |
| **FR2** | Group by day (3–7) | UC1 | §3.2 | TC1 |
| **FR3** | Order visits & show times | UC1 | §3.3 | TC1 |
| **FR4** | Hotel suggestion | UC2 | §3.4 | TC4 |
| **FR5** | Restaurants — Manual | UC3 | §3.5 | TC5 |
| **FR6** | Restaurants — Auto-Pick | UC4 | §3.6 | TC6, TC7 |
| **FR7** | Lock & Regenerate | UC5 | §3.7 | TC8 |
| **FR8** | Export (PDF/CSV/JSON) | UC6 | §3.8 | TC9 |

> Adjust SRS section numbers if yours differ.

### 2.2 Non-Functional Coverage (NFR ↔ SRS ↔ Test)
| NFR ID | Quality Target | SRS Section | Test ID(s) |
|---|---|---|---|
| **NFR1** | Performance: ≤10 s for ≤40 POIs | §5 | TC3 |
| **NFR2** | Usability: clear warnings | §5 | TC2 |
| **NFR3** | Security/Privacy basics | §5 | TC10 *(or N/A if no login)* |
| **NFR4** | Reliability: graceful fallbacks | §5 | TC7 |
| **NFR5** | Browser portability | §5 | Checklist |

---

## 3. Acceptance Test Plan

### 3.1 Pre-Test Setup (common)
- **City:** Pittsburgh  
- **Seed data:** ~20 POIs, 8 hotels, 20 restaurants  
- **Trip settings:** 3 days; Travel mode = Drive; Detour limit = 15 min  
- **Meal windows:** Lunch 11:30–14:00; Dinner 17:30–20:30  
- **Browser:** Chrome desktop  
- **Notes:** If login is not implemented, mark TC10 **N/A** and state it in results.

### 3.2 Test Cases

| Test ID | Name | Steps (user → system) | Expected Result |
|---|---|---|---|
| **TC1** | Generate 3-day plan | Add 15 POIs (3 must-go) → Click **Generate** | Plan shows Day 1–3; each day has ordered visits; per-day & total time visible. *(FR1–FR3)* |
| **TC2** | Must-go overload warning | Mark 10 POIs as must-go; set 2 days → **Generate** | Clear warning: “Too many must-go for 2 days. Add a day or uncheck items.” *(NFR2)* |
| **TC3** | Performance ≤10 s | With 40 POIs → **Generate** (start a timer) | Plan appears in **≤10 s**. *(NFR1)* |
| **TC4** | Choose hotel | Open **Hotel suggestions** → pick top result | Hotel attached to itinerary; travel times update; hotel marker visible. *(FR4)* |
| **TC5** | Restaurants (Manual) | Day 1 → Lunch → filter “Vegetarian, $$, open now” → pick | Lunch set for Day 1; detour within limit; day timing updates. *(FR5)* |
| **TC6** | Restaurants (Auto-Pick) | Toggle **Auto-Pick** (all days) | Lunch & dinner chosen per day; open hours respected; can swap. *(FR6)* |
| **TC7** | Auto-Pick fallback (closed) | Temporarily set all lunch candidates as “closed” | System picks nearest open fallback within detour limit and explains reason. *(FR6, NFR4)* |
| **TC8** | Lock & Regenerate | Lock 1 hotel + 2 POIs → **Regenerate** | Locked items preserved; remaining visits re-optimized; plan valid. *(FR7)* |
| **TC9** | Export JSON/PDF | **Export → JSON**, then **PDF** | Files contain ordered POIs, hotel, meals, times; JSON schema valid. *(FR8)* |
| **TC10** | Basic privacy | Attempt to open another user’s saved plan (if login exists) | Access denied/not visible; no data leakage. *(NFR3)* |

---

## 4. Validation Rules Checklist (for testers)
- Trip **days ∈ [3..7]**  
- Total **POIs ≤ 40**  
- Coordinates are valid numbers  
- **Daily time budget** not exceeded  
- Restaurant **open** within lunch (11:30–14:00) / dinner (17:30–20:30) window  
- **Detour ≤ 15 min** (or configured value)  
- Diet/price filters enforced when set  
- **Locks** persist after regenerate  
- Exports include **ordered POIs, hotel, meals, times**

---

## 5. Consistency Review (before running tests)
- **Names match** across all docs: *Generate, Lock, Regenerate, Export; Restaurants — Manual; Restaurants — Auto-Pick*.  
- **Numbers match**: Pittsburgh; 3–7 days; ≤40 POIs; detour 15 min; meal windows as above.  
- **Diagrams align**: UC1..UC6 names; class names (POI, DayPlan, etc.); sequence flows mirror UC main steps.  
- **Section refs**: SRS section numbers in the matrix match your actual SRS headings.

---

## 6. Exit Criteria
- Every **FR** appears in SRS §3, in at least one **Use Case**, and has ≥1 **Test Case**.  
- Every **NFR** is stated in SRS §5 and has a test or checklist item.  
- All tests **pass** or have a documented reason and follow-up.  
- No unexplained acronyms; wording is consistent.

---

## 7. Open Questions
All previously open items (daily time budget, detour limit, minimum hotel rating, meals required) are **resolved** in SRS §7 “Business Rules & Validation”.


---


