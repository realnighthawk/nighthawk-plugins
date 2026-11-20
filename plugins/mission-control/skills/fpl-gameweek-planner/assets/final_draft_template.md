# FPL GW[N] Final Draft - [team name] ([team id]), [league name] ([league id])

Deadline: [UTC time] ([user's local]). Chip this GW: [wildcard / none / ...]. Budget: £[x]m (app, selling prices). Goal: [climb / defend / maximise].
Position: [rank], [points]; leader [name] [points]. Data: official FPL data as of [time]; rivals' squads = GW[N-1] picks.

## Method (one line each)
1. Internet = hypotheses (research.md). 2. Statistics = confidence: E = blend of underlying model and realised points, per gameweek over GW[a]-GW[b] (stats.md). 3. League = overlay: managers ahead, their squads, ownership.

## Squad (£[cost]m, £[spare]m spare)
| Pos | Player | £m | E | e1 | Owned by managers ahead (of n) |
|---|---|---|---|---|---|

## Lineup
XI ([formation]): ...
Bench order: ...
Captain: [player] (e1 [x]); vice: [player]. Alternatives and their expected cost: ...

## Why (short)
- Changes versus last time and the number behind each.
- Template players kept (owned by all ahead): ...
- Differentials (owned by none ahead): ...
- Claims from the internet: confirmed [..], rejected [..] (with numbers).

## League overlay
Table: manager, points, chip played, captain, dead slots. What it means for this squad. Edge versus rivals is optimistic (same model chose the squad; rivals will transfer).

## Chips plan
Left: ... Plan: ... (the set's expiry is `boot.json`'s `stop_event`; check it.)

## Hold-period check (if the squad must last N weeks)
Per-gameweek weak spots, rotation, yellow cards, bench cover, uncovered positions.

## Risks
Top three, each with the evidence.

## Before you confirm
1. Cost <= budget in the app. 2. Team news (named players). 3. Chip active / captain set. 4. Deadline local time.

Files: `research.md`, `stats.md`, `final.md` in your working directory; the saved plan lives in the skill's data directory (`fpl_plan.state`).
