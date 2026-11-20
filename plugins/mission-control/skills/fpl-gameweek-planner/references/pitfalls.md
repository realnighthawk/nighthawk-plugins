# Audit checklist - mistakes this workflow has already made

Run through this before delivering. Each item is a real error from the session that produced this skill.

1. **Budget from list prices.** The app's budget is the selling value plus bank, and the price on each pitch card is the SELLING price. The FPL API gives purchase prices, not selling prices: `fpl_flow.profile` derives each player's selling price and prints the "For inputs.json" line - use it. A plan costed at current prices was £0.1m over. If the lookup fails, ask the person for the app's budget and selling prices and state the assumption; never substitute the current-price total.
2. **Chip rules recalled from memory.** A claim that the user could save triple captain/bench boost for a double gameweek in GW33 was wrong: first-set chips expire at the GW19 deadline and a fresh set starts at GW20. Check `chips` in the downloaded bootstrap data (`boot.json`: each chip has start/stop events) and the official chip announcement before asserting any chip rule.
3. **Hand-built shortlist.** Candidates taken from articles and tool outputs missed whole teams and good players (e.g. a Leeds defender, Arsenal options). Always screen the full pool by position with the script, then compare the web's names against it.
4. **Mixed metrics.** Using points per million, a tool's captain score, a model-only ranking and the blended score at different moments made one player look benchable and startable in consecutive answers. Use one score (`E` / `e1`).
5. **Tool "expected points" are form.** `ep_next` equals `form`; "captain X (EP 10.5)" suggestions are form artefacts. Don't cite them as forecasts.
6. **Rivals' squads are last gameweek's.** Say so. Their dead slots (injured players) will be fixed before the deadline, so the edge table is optimistic.
7. **Selection bias.** The optimised squad always beats others on its own model. Present edges as direction, not forecast. Optimum within ~2% of the user's draft = noise.
8. **Recency vs results.** A model-only view benched an in-form defender whose real points were far above his xG; the blended score fixed it. If the model and results disagree strongly, say which you trusted and why.
9. **Concentration vs spread.** Several players from one team (especially away at a strong side) are correlated; check teams not in the squad were at least screened, and mention correlated risk plus natural hedges (an opposing forward in the same match).
10. **Time and deadline.** The deadline is in UTC in the data (`meta.json`); the user's screen shows local time. Convert and remind. Lineups come after the deadline - team news before it overrides the model.
11. **Wildcard = hold period.** If the user won't transfer for a couple of weeks, evaluate GW+1 and GW+2 too (the weekly table), plus rotation, yellow cards (check the season's accumulation rule), bench cover (a bench goalkeeper who never plays gives nothing), and positions with no cover (three forwards, all starters).
12. **Ambiguous names.** `Thomas` matches several players; use `Name:TEAM`. A zero-minute player has no score - fine for bench fodder, flag it.
13. **Unverified claims in prose.** Every number in the answer must come from a script run in this session; every fact (injury, fixture, rule) from a check, not recall.
14. **Confusing the user.** If the user asks "why X over Y", answer with the same metric and the raw facts side by side (points, goals, clean sheets, xGC, price, fixtures), then the verdict. Admit changes of mind explicitly and say what caused them.
