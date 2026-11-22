# Method: the score, the league logic, the limits

Read this when you need to explain a number or defend a choice. Contents: score, per-player fields, league logic, optimiser, limits.

## The score (what `model` computes)

For every player, for each gameweek in the horizon (default 5):

- **Underlying part (xp)** - expected points from per-90 underlying stats, adjusted for the opponent and venue, times minutes share.
  - Attack: goals and assists from xG/xA per 90, scaled by how leaky the opponent is (`opponent xGA / league average`, +10% at home, -10% away).
  - Defence: clean-sheet chance `exp(-expected goals conceded)` where expected conceded is the player's xGC per 90 scaled by the opponent's attack (`opponent xGF per game / league average`, venue-adjusted).
  - Points: appearance 2; goal 6/5/4 (DEF/MID/FWD); assist 3; clean sheet 4 (GK/DEF) or 1 (MID); -0.5 per expected goal conceded (GK/DEF); defensive-contribution bonus 2 with a Poisson chance of reaching the threshold (10 DEF, 12 MID/FWD) from the per-90 rate; average bonus per start; GK saves/3.
  - Team strength is derived from player data (team xG / games, goalkeeper xGC per 90) because the API's own strength fields can be zeroed.
  - Double gameweeks add fixtures; blanks give zero.
- **Realised part** - the player's season points per appearance times minutes share times number of fixtures.
- **e (per gameweek)** = availability x (blend x underlying + (1 - blend) x realised); default blend 0.5. Availability is 0 for injured/suspended/unavailable, chance/100 for doubts.
- **E** = sum of e over the horizon. **e1** = first gameweek only (used to choose the XI and captain).

Why a blend: underlying numbers (xG etc.) are less noisy than results but ignore real traits (set pieces, finishing, bonus); results are noisy over ~7 games. Equal weight regresses outliers about halfway. Players with few minutes are discounted by minutes share.

Why not the tool/website "expected points": in this data `ep_next` equals `form` for the players checked, so it is not an independent forecast.

## Fields in `players.json`

`E`, `e1`, per-gameweek `e` and `xp`, `fixtures` (labels), `mshare` (minutes share, rotation proxy), `ppg` (points per appearance), `xgi90`, `xgc90`, `dc90`, `yellows`, set-piece orders, `avail`, price/ownership. After `league`, the optimiser/evaluator add `ahead` (managers ahead of the user who own the player), `all`, and `L` (league-aware score).

## League logic

Let rivals' squads be fixed. Expected gain versus a rival = sum over players of expected points x (you own - they own). Therefore:

- A player both of you own contributes zero to the gap. A strong player they own and you don't is exposure (you lose ground if he scores).
- Maximising your own expected points already maximises expected gain over every rival. Ownership does not change expectation - it changes **variance**.
- When behind, extra variance helps, so among near-equal candidates (within roughly 1-3 score points) prefer the one the managers above you don't own. The `L` score adds up to +10% for players none of them own; it is a tie-breaker, not a reason to give up real points.
- Do not drop template players (owned by every manager ahead) without a clearly better alternative: selling them adds exposure with no edge.
- Captain: if everyone captains the same player, matching him gains nothing on them but is usually still the best expected pick. A differential captain costs its expected-score gap (shown by `evaluate`) and only pays when he outscores the template pick; choose it only when the gap is small or the user wants variance.
- Correlation: players in the same match (your defenders and an opposing forward of yours) partly hedge each other; several attackers from one team rise and fall together. Mention it; don't over-engineer it.
- The edge-over-rivals table is optimistic: the squad is chosen by the same model, and rivals will fix dead slots before the deadline. Direction only.

## Optimiser (`optimize`)

Simulated annealing over 15 slots (2 GK, 5 DEF, 5 MID, 3 FWD) with the budget, max 3 per club, availability >= 75%, and players with few minutes only if cheap (bench fodder). Objective = best XI by formation + 0.12 x bench. It prints an EV-only squad (`E`) and a league-aware squad (`L`). Seeds are fixed so runs repeat. `force` pins players, `exclude` removes them. `sell` applies only to players the user already owns; other players cost their current price.

## Limits worth stating to the user

- About 7 gameweeks of data early in a season; per-90 rates are noisy. Treat gaps under ~2% as noise.
- Picks used for rivals are last gameweek's; they will transfer.
- The model does not know about injuries not yet in the data, European rotation, manager quotes or lineups. Team news before the deadline overrides it.
- It does not value price changes, template effects beyond ownership counts, or fixture swings beyond the horizon.
