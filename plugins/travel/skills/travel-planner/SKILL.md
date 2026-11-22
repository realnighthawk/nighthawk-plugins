---
name: travel-planner
description: Plans a trip: finds or creates it in TREK, researches places with maps, and writes the itinerary, bookings, budget and packing into TREK. Use whenever the person mentions a trip, travel, a vacation, a holiday, an itinerary, flights, hotels, a route or places to visit ("plan my Lisbon trip", "add this to my Japan trip", "where should we stay in Porto").
---

# Planning a trip

TREK is the record for the trip itself: its days, places, bookings, budget, packing, and the people on it. The Life engine
holds the person's own commitments around the trip: one goal with the actions and reminders that must happen before, during
and after it. `maps` is the research and routing layer: compare places, order a day, check distances and weather, then
write the result into TREK. Keep those roles separate; a record copied into two places drifts.

Call each server's tools directly, using the names and schemas it advertises: `trek` for the trip, `maps` for
places and routes, `life` for the person's commitments. Tool names are fully qualified: `trek:<name>`,
`maps:<name>`, `life:<name>`.
The TREK surface is large and versioned: do not guess a tool name or an id. Resolve trip, day, place and member ids from
`trek:list_trips`, `trek:get_trip_summary` or the matching `trek:list_*` first. If no `trek` tool is found, say travel planning is not
connected and stop; do not fake it with notes. If a maps or Life tool is missing, use what is connected and say what is not.

A new trip gets a Life goal. A change to a trip that already exists does not create a second one. If the person only asks
for one place, one booking or one day, do that and leave the rest alone.

The mechanical parts are in `scripts/travelplan.py`: `rank`, `check` and `reminders`. Use them for preference ranking,
itinerary arithmetic and reminder dates; keep the judgement — which places, which order, what to drop — for yourself.

## 0. Personalize it

Preferences are not decoration: pace, budget, interests, who is travelling and what they cannot do change which places
survive, how many fit in a day, and what a good day costs. Treat them in two tiers:

- **Hard — never violate:** the `never` list, mobility and accessibility needs, dietary needs, infants and young children,
  the dates, and the budget ceiling. If a must-see conflicts with a hard constraint, say so and ask; do not silently drop
  either.
- **Soft — weights, not rules:** interests, priorities, crowd tolerance, walking tolerance, loyalty programmes and the
  preferred pace. Use them to choose between good options, not to overrule a hard one.

The script turns those into consequences: `relaxed` caps a day at four stops, `shoestring` penalises expensive places,
`minimize_transit` doubles the distance penalty, `must_see` outweighs every soft signal, and `never` removes a place
outright. Change a preference and the shortlist should visibly change; if it does not, the preference did not reach the
candidates.

At the start, recall travel preferences with whatever memory tools are available, and read the person's time zone with
`life:settings_get`; use that time zone as the home zone. Ask for anything that
is missing or ambiguous and would change the plan — the destination, dates, who is going, budget, pace, or a preference
that conflicts with a hard constraint — one thing at a time; do not interrogate. Use what you already know first: if a
recalled preference applies, put it in `preferences.json`, state the plan around it in the person's terms ("you like food
and history, so I'll keep the days walkable and leave room for markets"), and do not ask them to repeat it. Write the
merged result to `preferences.json`:

```json
{"pace":"balanced","budget":"mid","interests":["food","history"],"priorities":["food","minimize_transit"],
 "travelers":{"adults":2,"children":0,"infants":0},"mobility":"full","dietary":[],"home_airport":"SFO",
 "currency":"USD","time_zone":"America/Los_Angeles","must_see":["Belém Tower"],"never":["nightclubs"],
 "max_daily_travel_minutes":90,"day_start":"09:00","day_end":"21:00"}
```

There is no separate save call: the conversation is retained, so state a newly learned preference plainly and reuse it in
the plan.

## 1. Find or start the trip

Call `trek:list_trips` first. If the person named a trip, use it. If they are starting one, confirm the destination,
the dates and the currency, then `trek:create_trip`; days are generated from the date range. Call
`trek:get_trip_summary` before non-trivial changes, every time: TREK changes live and other members may be editing it.

Call `life:intentions_list` and `life:tasks_list` too. If a goal (an intention) for this trip already exists, reuse it and add only
what is missing; never create a second goal for the same trip.

## 2. Set up the Life side

One goal for the trip, in the person's words, with `ends_on` the return date; put the TREK trip id in its notes. Then choose
the actions TREK does not hold: passport or visa, vaccinations, insurance, a booking still to make, online check-in,
packing, the house while away. Do not hand-compute their dates. Write `brief.json`:

```json
{"trip_title":"Lisbon","trip_id":42,"departure":"2026-06-03T10:00","return":"2026-06-10T22:00",
 "home_time_zone":"Europe/Lisbon","international":true,"currency":"EUR","passport_expiry":"2030-01-01",
 "goal_id":"<existing goal id, only when the goal already exists>",
 "rules":["passport","check_in","pack"],
 "custom":[{"title":"Book the Douro tour","days_before":7,"time":"10:00","alert_before_minutes":0}]}
```

`departure` and `return` are local wall-clock times in `home_time_zone`, with no zone suffix; `return` may be a date.
`trip_id` and `goal_id` are optional; `passport_expiry` is needed only for the `passport` rule on an international trip.
The rules are `passport`, `visa`, `vaccinations`, `insurance`, `check_in`, `pack`, `house`, `currency`, `roaming`, `car`,
`gear`, `restaurant`, `documents`, and `custom` items. Then run:

```bash
python3 scripts/travelplan.py reminders brief.json preferences.json
```

It returns the goal line, the dated tasks with alerts, and `operations`. Fix every `problem`; read `warnings` for tasks
already in the past (skip them and say so). Then call `life:batch_apply` with a fresh `idempotency_key` and
`operations`: it creates the goal and the tasks, each linked to the goal, all or nothing. If the goal already exists, put its id in
`brief.json` as `goal_id` and rerun, and the operations create only the tasks and their links.

Work you must do later or on a repeat ("check flight prices every Tuesday") is an agent task: `subject: "agent"`, an `at`,
an alert, and the job itself in the title and notes. It wakes this conversation.

Do not mirror the itinerary, flights, hotels, reservations, budget or packing into Life. Those are TREK's records, and a
second copy goes stale. A TREK to-do is shared with the trip's members; a Life task is the person's own reminder. Use TREK
to-dos for what the group shares and Life tasks for what the person must personally do.

## 3. Research with maps, record in TREK

Use maps to decide and TREK to keep:

- Resolve the base and candidate places with `maps:geocode`, `maps:search_places`,
  `maps:search_nearby` and `maps:get_place_details`.
- Order a day with `maps:plan_route`; check legs and feasibility with `maps:get_directions` and
  `maps:get_distance_matrix`; use `maps:get_elevation` for a hike, `maps:get_weather` for the dates,
  and `maps:get_timezone` when the trip crosses zones.

Write the candidates to `candidates.json` (`name`, `types`, `rating`, `ratings_count`, `price_level`, `distance_km`,
`tags`) and run:

```bash
python3 scripts/travelplan.py rank candidates.json preferences.json --top 15
```

The ranking is a shortlist, not a decision: must-sees first, interests and priorities weighted, budget and distance
penalised, `never` excluded. Apply the hard filters first — `never`, dietary, accessibility — then rank what is left; a
score cannot fix a place that cannot feed them or cannot be entered. You still choose for fit, opening hours and the shape
of the day; never let a score override a hard constraint.

- Write the chosen place into TREK. `trek:search_place` returns the `osm_id`/`google_place_id` that makes TREK show
  hours, ratings and map links; `trek:create_place` also accepts `lat`/`lng` from maps. Prefer TREK's search when it finds the
  same place.

Never invent a coordinate, price, opening time, flight number or airport code. Resolve it or ask. A weather forecast far
from the date is a trend, not a fact: say so.

## 4. Build the TREK side

Before creating anything in TREK, write the day-by-day shape to `plan.json` (dates, day windows, stops with duration,
travel time and opening hours, and budget) and run:

```bash
python3 scripts/travelplan.py check plan.json preferences.json
```

It catches a stop that runs past the day, a closed stop, too many stops for the pace, too much daily travel, a day outside
the dates or twice, and budget currency or target errors, and returns the total and per-person budget for the recap. Fix
every problem before the first TREK write. The shape is:

```json
{"start":"2026-06-03","end":"2026-06-10","currency":"EUR","travelers":2,
 "days":[{"date":"2026-06-03","start":"09:00","end":"21:00",
          "stops":[{"name":"Belém Tower","duration_minutes":90,"travel_minutes_from_prev":25,
                    "opens":"10:00","closes":"18:00"}]}],
 "budget":{"target":2000,"items":[{"category":"lodging","amount":800,"currency":"EUR"}]}}
```

- **Days and places.** `create_day`/`update_day` for titles and notes; `create_and_assign_place` for a new place on a day,
  `assign_place_to_day` for an existing one; `update_assignment_time`, `move_assignment` and `reorder_day_assignments` to
  shape the day. `set_assignment_participants` when only some members join.
- **Transport and stays.** `search_airports` before a flight; `create_transport` for flights, trains, cars and cruises
  (endpoints, times, price, status); `create_reservation` for hotels, restaurants, tours and other bookings;
  `create_accommodation` or `link_hotel_accommodation` to tie a stay to days. Bookings are `pending` by default: leave them
  pending until the person says it is booked, then confirm with `update_transport`/`update_reservation`.
- **Money.** `create_budget_item_with_members` (or `create_budget_item` plus `set_budget_item_members`),
  `update_budget_item`, `get_settlement_summary` and `create_settlement`. Use the trip's currency; resolve splits with
  `list_trip_members`. A planning estimate is a note, not a booked price.
- **Packing.** `list_packing_templates` then `apply_packing_template` (or `bulk_import_packing`);
  `create_packing_bag`/`set_bag_members`; `toggle_packing_item` as things are packed.
- **Group work.** `create_todo` for shared trip to-dos; `create_collab_note` and the Collab tools when the addon is on;
  `create_share_link` for a read-only link; `export_trip_ics` when they want the trip in a calendar.

After a change, call `trek:get_trip_summary` and recap what changed. Do not read the whole itinerary back unless it is new.

## 5. The wider TREK surface

Use the tool names `trek` advertises. The areas are:

| Area | What it adds |
|---|---|
| Trips | `update_trip` (dates, currency, archive), `copy_trip`, members, share links, `.ics` |
| Places | categories and tags, `import_places_from_url` (a public Google/Naver Maps list), `resolve_maps_url` |
| Day planning | day notes, participants, timed assignments, reordering |
| Bookings | 6 reservation types (hotel, restaurant, event, tour, activity, other), 4 transport types, `search_transit_routes` → `create_transit_journey` |
| Money | splits, payers, settlements in the trip's base currency |
| Packing | templates, bags, category assignees |
| To-dos | shared lists, categories, assignees |
| Collab *(addon)* | notes, polls, chat, reactions |
| Atlas *(addon)* | visited countries/regions, stats, bucket list |
| Vacay *(addon)* | leave, public holidays, carry-over |
| Journey *(addon)* | multi-trip journeys, entries, share links |
| Weather/airports | TREK's own `get_weather`, `get_detailed_weather`, `search_airports` |

The Journey journal, photo-book designer, file uploads, PDF export and cover images are web-UI features; TREK's MCP
surface does not expose them. Point the person to the web UI, or use the `browser` skill when it is available
and they ask you to do it there. Do not promise them from the MCP surface.

## 6. If something is unavailable

Atlas, Collab, Vacay and Journey are addons: if a tool is missing or a call is out of scope, name the addon or scope that is
needed and carry on with the rest. TREK's OAuth connection belongs to the person; if it fails to authorize, tell them to
reconnect it through the service. Do not silently drop the request.

Missing maps or TREK tools: the `browser` skill, when available, is the fallback for what the person can
see on the web - research a place, read a TREK page, use a web-UI-only feature they asked for. It does not replace a TREK
write: do not hand-enter an itinerary through the UI unless the person asked for that, and never keep a second copy.

## 7. Guardrails

- Do not confirm a pending reservation or transport booking unless the person says it is confirmed.
- Do not delete a place, day, trip or member without saying what will be removed; `bulk_delete_places` cannot be undone.
- Do not copy a TREK record into Life, or a Life reminder into TREK, to "keep them in sync".
- Do not create a trip, goal or reminder for a passing wish ("I'd love to go to Japan"); offer first.
- Do not use this skill for a non-travel goal; that is `manage-goals`.

Reply with the trip, the days, the bookings (and what is still pending), the budget, the Life reminders, and what you need
from them.
