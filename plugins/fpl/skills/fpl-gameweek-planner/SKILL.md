---
name: fpl-gameweek-planner
description: Plans a Fantasy Premier League (FPL) gameweek end to end - wildcard drafts, free-hit/bench-boost/triple-captain timing, transfers, starting XI, captain, and how to climb a mini-league. Combines community research (articles, Reddit, podcasts) as hypotheses, full-player statistics as the confidence check, and rivals' real squads as the league overlay, then writes a final draft. Use this whenever the user mentions FPL, fantasy premier league, a gameweek (GW8 etc.), wildcard, captain pick, "who should I transfer", their FPL team id or mini-league id, rank climbing, or wants to continue/redo an earlier FPL plan - even if they don't say "skill".
---

# FPL gameweek planner

Plan one Fantasy Premier League gameweek: what the team should look like, and how to climb the mini-league. Work in your
working directory; each step leaves a file the next reads. The deterministic half is the installed helper:

```bash
python3 scripts/fpl_flow.py <command> ...
```

It fetches and scores from the public FPL API and keeps its data under `~/.fpl-planner` (override with `FPL_DATA_DIR`).
Call the FPL tools directly when they are connected: `fpl__*` for facts and `fpl-intelligence__*` for advice, using the schemas
the tools advertise. Tools are named `<service>__<tool>` (the hub's name). Your harness may put a prefix in front of that name; match by the `<service>__<tool>` ending and never invent a prefix. If neither is connected, the helper still fetches and scores from the public API; use it
for everything except the profile and rival overlays.

Principles to keep throughout:

- One score for everyone. Switching metrics mid-way (points per million, a tool's captain score, a model-only ranking) produced contradictory advice before; if you must use another number, say why and don't let it overrule the main score.
- Explain verdicts with the number, in plain language; say when something is a judgement call or inside the model's noise.
- Selection bias: the model-picked squad will always look better than rivals on the same model. Present edges as direction, not forecast.
- Never claim a chip, price, injury or rule fact you have not checked this session.
- Do not fetch FPL data by hand: the numbers come from the helper and the `fpl` tools.

## 1. Scope: collect the inputs, on your own

The only thing you must ask for is the team id (the number in the URL `fantasy.premierleague.com/entry/<ID>/event/N`), if
the request does not give it. Everything else: get it, work it out, or choose a default and say so. Ask only if a wrong
guess would cost the person something.

- **Profile.** `fpl-intelligence__fpl_manager_hub` with `team_id: <ID>` returns the bank,
  free transfers, chips used and available, injured players, price moves and the squad. Save the reply to `hub.json` and
  run `python3 scripts/fpl_flow.py profile hub.json --team <ID>` for the distilled lines and the private leagues. Read
  the fields you need; do not paste the whole reply into the plan.
- **Selling prices.** Run `python3 scripts/fpl_flow.py selling <ID> --bank <bank>`. It prints the selling price of every player and the TRUE
  BUDGET (selling value plus bank), with a "For inputs.json" line. Use those numbers; never ask the person for the bank,
  free transfers, chips, prices or budget. If it raises, say what failed and ask only for what is missing.
- **League.** `fpl__get_manager_info` with `team_id: <ID>` lists the person's
  leagues. A private classic league (`league_type` `x`) is the one to use. If the request names one, use it. If there is
  exactly one private classic league, use it. If there are several, ask once with exactly the leagues as options and no
  "both" (one league per plan; the choice changes who the rivals are), and keep the answer. If there is none, leave it
  empty.
- **Goal.** Use what the person said. If nothing: "climb" when they trail the leaders, "defend a lead" when they lead,
  else "just maximise points". Say which.
- **Must-keep / must-avoid.** None, unless the person named some.
- **Saved state.** Run `... fpl state <ID>`. If it shows a previous plan, say what it decided, reuse its league, and
  continue from it.

Write `inputs.json` in this shape:

- `team`: the numeric team id; `league`: the numeric league id, or "" when there is none;
- `goal`: "climb", "defend a lead" or "just maximise points";
- `budget` and `sell`: exactly the "For inputs.json" values from `fpl selling`;
- `chips`: the chips available for the coming gameweek, as the profile lists them;
- `force` and `exclude`: player names the person asked to keep or avoid, "" if none;
- `assumptions`: everything you chose instead of being told (each short), so the report can state it.

Then run `python3 scripts/fpl_flow.py scope inputs.json`. It passes only when the file holds what the later steps need; fix what it says and
run it again.

## 2. Fetch and score

Run `python3 scripts/fpl_flow.py fetch <ID> [--league <league id>]`. It reads the public FPL API, scores every player over a five-gameweek
horizon, and writes the tables to `fpl-output.txt`. No model work here.

When there is a league, get the rival overlay:

1. `fpl-intelligence__rival_tracker` with `league_id: <L>` and `team_id: <ID>`.
2. Save the reply as `rivals.json`.
3. Run `python3 scripts/fpl_flow.py rivals rivals.json`; it writes `rivals.md` with the standings, recent transfers and likely next moves.

## 3. Research (internet = hypotheses)

Follow [references/research.md](references/research.md). In short: gather consensus on captains, injuries,
buys/sells, wildcard drafts and chip timing from articles (`exa__web_search_exa`, then `exa__web_fetch_exa`), r/FantasyPL via
`reddit__browse_subreddit`, podcast/YouTube titles, and `fpl` facts. Output a table of **claims to
test** (player/idea, source, direction) to `research.md`. Do not decide anything here.

When a research tool is missing, blocked, or weaker than the site itself, use oh-my-pi's built-in browser when it is
available: the FPL site, the subreddit, an article that returns 403, a video's transcript page. It is read-only unless
the person asked for that exact action; never post, reply, follow or transfer from it.

## 4. Test the claims against the numbers

`fpl-output.txt` is the statistics layer, already fetched and scored: every player scored over a five-gameweek horizon
from the official FPL data. Read its tables; details of the score are in
[references/method.md](references/method.md) (read it once if you need to explain a number).

For each claim, find the player in the helper output (or run `fpl__get_player_information` for gameweek-by-gameweek
minutes and form, `fpl__analyze_player_fixtures` for the next fixtures) and record a verdict with the number: confirmed /
rejected / unclear. A web claim the stats don't support is rejected, however popular. A strong stats pick the web never
mentioned is fine - the web is a shortlist, not a gate.

Save the verdicts, each with its number, to `stats.md` (numbers only: no opinions). Picks used for rivals are from the
**last finished** gameweek: other managers' picks for the upcoming gameweek are not public before the deadline. Say so
whenever you quote rival squads.

## 5. Draft, with the league overlay

Read `rivals.md` for who is ahead, which chips they have used, their captains and dead starters, then apply the rules in
[references/method.md](references/method.md) ("League logic"):

- Owning what every manager ahead owns is neutral; not owning it is exposure. Keep template players unless a clearly better pick exists.
- Differentials (nobody ahead owns them) are where ground is gained - prefer them only when their score is within noise of the alternative.
- Expected value does not depend on ownership; ownership only changes variance. Do not give up real expected points for a differential.

Run:

```bash
python3 scripts/fpl_flow.py optimize <ID> --budget <budget> --sell "<Name=price,...>" [--force "A,B"] [--exclude "C"]
python3 scripts/fpl_flow.py evaluate <ID> --budget <budget> --sell "<...>" --squad "<15 names>"
```

`optimize` gives an EV-only squad and a league-aware squad as a **starting point**. If the optimum beats the user's draft
by under about 2% it is inside the model's noise - keep the draft. Use `evaluate` on the squad you settle on: it prints
the weekly table, best XI per formation (near-ties are decided by the league overlay and by correlation), captain
candidates with their expected cost, exposure, flags (doubts, minutes, yellow cards) and the optimistic edge over rivals.
Use `Name:TEAM` when a surname is ambiguous (`Thomas:COV`).

Captain: default to the highest first-gameweek score. Only recommend a differential captain when the expected cost is
about a point or less or the person has said they want variance; state the cost.

Chips: read [references/chips.md](references/chips.md), and check the real schedule with
`fpl__get_blank_gameweeks` and `fpl__get_double_gameweeks`. The season's chip sets and their expiry are in the bootstrap data the
helper downloaded (`~/.fpl-planner`): check them, do not recall them.

If the person planned to hold the squad for N weeks (typical after a wildcard), read the per-gameweek columns, not just
the first: check for a bad run of fixtures, rotation risk, suspension risk, and whether bench cover is real.

Cross-check the draft, never override it: `fpl-intelligence__chip_strategy` for chip timing, `fpl-intelligence__is_hit_worth_it` before
you recommend a hit, and `rivals.md` for the overlay. Their numbers are a second opinion; the helper's score decides.

Under a heading "Numbers" in `final.md`, copy the figures that `optimize` and `evaluate` print (the draft's horizon score,
the EV-only optimum, the league-aware optimum, the XI and captain edges). Later steps read your files, not your tool
output, so a number that is not in `final.md` cannot be cited.

Write the draft to `final.md` from [assets/final_draft_template.md](assets/final_draft_template.md).

## 6. Audit before delivering

Run the checklist in [references/pitfalls.md](references/pitfalls.md). It exists because earlier plans went
wrong in specific ways (budget from list prices, a stale chip rule, a hand-picked shortlist missing whole teams, mixing
different metrics so answers contradicted each other). Quick version: one metric throughout; budget is the app's
selling-price budget; every team/position was screened by the helper rather than by memory; claims about rules are
checked, not recalled; any number quoted comes from a run this session.

Write `audit.md`: each item of the checklist with pass or what you fixed in `final.md`. Fix `final.md` itself where an
item fails.

## 7. Deliver and save state

Finish `final.md`. In the reply: squad, XI, bench order, captain/VC, chip plan, what changed versus last time, and the
top risks - in that order, short. Then save state:

```bash
python3 scripts/fpl_flow.py state <ID> --write '{"gw": N, "budget": 100.1, "squad": ["..."], "xi": ["..."], "captain": "...", "vice": "...", "chips": {"left": ["..."], "plan": "..."}, "decisions": ["kept X: template"], "open_questions": []}'
```

Run `python3 scripts/fpl_flow.py state <ID>` again and do not end until it shows the plan. If the
`view-builder` skill is available, use it for the result; otherwise skip it.
