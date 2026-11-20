"""The FPL steps that are not the model's judgement: distill a tool reply, derive selling prices, check inputs, fetch and
score, format rivals, and save state.

Run from the skill directory:

  python3 scripts/fpl_flow.py profile hub.json [--team <ID>]
  python3 scripts/fpl_flow.py selling <ID> --bank <millions>
  python3 scripts/fpl_flow.py scope inputs.json
  python3 scripts/fpl_flow.py fetch <ID> [--league <L>]
  python3 scripts/fpl_flow.py rivals rivals.json
  python3 scripts/fpl_flow.py optimize <ID> --budget <B> --sell "<Name=price,...>" [--force "A,B"] [--exclude "C"]
  python3 scripts/fpl_flow.py evaluate <ID> --budget <B> --sell "<...>" --squad "<15 names>"
  python3 scripts/fpl_flow.py state <ID> [--write '{"gw": 9}']

The MCP servers are reached by the model, not here: this script reads public FPL API data and the JSON the model saves from
a tool reply. Every failure prints one JSON object with `problems` and exits non-zero.
"""

import argparse
import contextlib
import io
import json
import sys
import urllib.request
from pathlib import Path

import fpl_plan

API = "https://fantasy.premierleague.com/api"


class StepFailed(Exception):
    """The step is not done; the message says why and what to do."""


def unwrap(value):
    """A tool reply as the client hands it over: the object itself, or {"result": ...} around it, or a JSON string."""
    if isinstance(value, dict) and set(value) == {"result"}:
        value = value["result"]
    if isinstance(value, str):
        value = json.loads(value)
    return value


def api_get(path: str):
    request = urllib.request.Request(f"{API}/{path}", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)
    if data is None:
        raise OSError(f"{path}: not available")
    return data


def selling_prices(squad_ids: list[int], elements: list[dict], transfers: list[dict]) -> list[dict]:
    """What each player in the squad would fetch if sold now. FPL pays the purchase price plus half the rise, rounded down to
    0.1m, and the current price when it has fallen. The purchase price is the price paid in the latest transfer for the
    player, else his start-of-season price (a player never transferred in was in the first squad). Prices are in tenths."""
    by_id = {e["id"]: e for e in elements}
    bought = {}
    for t in sorted(transfers, key=lambda t: t["time"]):
        bought[t["element_in"]] = t["element_in_cost"]
    rows = []
    for element_id in squad_ids:
        e = by_id[element_id]
        now = e["now_cost"]
        purchase = bought.get(element_id, now - e["cost_change_start"])
        sell = now if now <= purchase else purchase + (now - purchase) // 2
        rows.append({"name": e["web_name"], "purchase": purchase, "now": now, "sell": sell})
    return rows


def summarize_selling(rows: list[dict], bank_tenths: int) -> str:
    sell = sum(r["sell"] for r in rows)
    now = sum(r["now"] for r in rows)
    budget = sell + bank_tenths
    return (
        "Selling prices (derived from the price paid for each player): " + ", ".join(f"{r['name']} {r['sell'] / 10:.1f}" for r in rows) + ".\n"
        f"Squad sells for {sell / 10:.1f}m + bank {bank_tenths / 10:.1f}m = TRUE BUDGET {budget / 10:.1f}m "
        f"(the same squad is worth {now / 10:.1f}m at current prices: do not use that).\n"
        "For inputs.json: \"budget\": " + f"{budget / 10:.1f}" + ", \"sell\": \"" + ",".join(f"{r['name']}={r['sell'] / 10:.1f}" for r in rows) + "\""
    )


def summarize_leagues(entry: dict, sizes: dict[int, int]) -> str:
    """The private classic leagues the team is in (league_type 'x'), with the rank in each and its size."""
    mine = [l for l in entry.get("leagues", {}).get("classic", []) if l.get("league_type") == "x"]
    if not mine:
        return "Private classic leagues: none (no league overlay is possible)."
    rows = [f"{l['name']} (id {l['id']}, you are {l.get('entry_rank')} of {sizes.get(l['id'], '?')})" for l in mine]
    return "Private classic leagues: " + "; ".join(rows) + "."


def names(rows, key="name", limit=4) -> str:
    return ", ".join(str(r.get(key)) for r in (rows or [])[:limit] if isinstance(r, dict) and r.get(key)) or "none"


def summarize_profile(hub: dict) -> str:
    status = hub.get("manager_status", {})
    health = hub.get("squad_health", {})
    mine = {p.get("name") for p in hub.get("squad", []) if isinstance(p, dict)}
    preds = hub.get("price_predictions", {})
    risers = [p["player"]["name"] for p in preds.get("likely_risers", []) if p.get("player", {}).get("name") in mine]
    fallers = [p["player"]["name"] for p in preds.get("likely_fallers", []) if p.get("player", {}).get("name") in mine]
    used = ", ".join(f"{c.get('name')} (GW{c.get('gameweek')})" for c in status.get("chips_used", [])) or "none"
    lines = [
        f"FPL profile, team {hub.get('team_id')}: gameweek {hub.get('gameweek')} done, preparing {hub.get('prepping_for')}.",
        f"Overall rank {status.get('overall_rank'):,}, {status.get('total_points')} points." if isinstance(status.get("overall_rank"), int)
        else f"{status.get('total_points')} points.",
        f"Bank {hub.get('bank')}m, free transfers {status.get('free_transfers')}, squad value {hub.get('squad_value')}m. "
        f"The tool's total_budget {hub.get('total_budget')}m is at CURRENT prices: the true budget is the selling value plus "
        "the bank, printed below.",
        f"Chips already played: {used}. Available for {hub.get('prepping_for')}: "
        f"{', '.join(status.get('chips_remaining', [])) or 'none'} (a chip played in a past gameweek, wildcard included, "
        "is not available again until its set resets; the set's events are in the bootstrap data).",
        "Injured or doubtful: " + (", ".join(f"{p.get('name')} ({p.get('status')})" for p in health.get("injured_or_doubtful", [])) or "none"),
        "Poor-form starters: " + (", ".join(f"{p.get('name')} ({p.get('form')})" for p in health.get("poor_form_starters", [])) or "none"),
        f"Price moves tonight touching the squad: rising {', '.join(risers) or 'none'}; falling {', '.join(fallers) or 'none'}.",
    ]
    return "\n".join(lines)


def summarize_rivals(rt: dict) -> str:
    me = rt.get("your_position", {})
    lines = [f"League {rt.get('league_name')} ({rt.get('total_managers')} managers), standings as of GW{rt.get('standings_as_of_gw')}: "
             f"you are {me.get('rank')} with {me.get('total_points')} points."]
    for r in rt.get("rivals", []):
        lines.append(f"- #{r.get('rank')} {r.get('team_name')} ({r.get('manager_name')}) {r.get('total_points')} pts, "
                     f"{abs(r.get('point_gap', 0))} {r.get('gap_direction')}; same captain: "
                     f"{'yes' if r.get('captain', {}).get('same_captain') else 'no'}; shares {r.get('shared_players')} players")
        if r.get("weaknesses"):
            lines.append("    weaknesses: " + "; ".join(r["weaknesses"]))
        moves = [f"in {t['in']['name']} / out {t['out']['name']} (GW{t['gameweek']})" for t in r.get("recent_transfers", [])[:4]
                 if isinstance(t, dict) and t.get("in") and t.get("out")]
        if moves:
            lines.append("    recent transfers: " + "; ".join(moves))
        pred = r.get("transfer_prediction", {})
        if pred:
            lines.append(f"    likely next: out {names(pred.get('likely_transfers_out'), limit=3)}; in {names(pred.get('likely_transfers_in'), limit=3)}")
    if rt.get("strategy"):
        lines.append("Tracker's strategy notes: " + " | ".join(rt["strategy"][:4]))
    return "\n".join(lines)


def load_inputs(path: str = "inputs.json") -> dict:
    try:
        inputs = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise StepFailed(f"cannot read {path}: {e}. The scope step must write it.")
    if not str(inputs.get("team", "")).strip().isdigit():
        raise StepFailed(f"{path} needs a numeric FPL team id under \"team\", got {inputs.get('team')!r}")
    return inputs


def scope_problems(inputs: dict) -> list[str]:
    problems = []
    if not str(inputs.get("team", "")).strip().isdigit():
        problems.append('"team" must be the numeric FPL team id')
    league = str(inputs.get("league", "")).strip()
    if league and not league.isdigit():
        problems.append(f'"league" must be ONE numeric league id (or empty), got {league!r}: pick a single league, not a list')
    try:
        float(inputs.get("budget"))
    except (TypeError, ValueError):
        problems.append('"budget" must be a number: copy it from the profile\'s "For inputs.json" line')
    if not isinstance(inputs.get("chips", []), list):
        problems.append('"chips" must be a list')
    if not str(inputs.get("goal", "")).strip():
        problems.append('"goal" is missing: say it, or choose the default and list it under "assumptions"')
    return problems


def run_planner(**arguments) -> str:
    """`fpl_plan.run_all(**arguments)`, returning what it printed."""
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            fpl_plan.run_all(**arguments)
    except fpl_plan.PlannerError as e:
        raise StepFailed(f"the planner stopped:\n{(out.getvalue() + str(e))[-1200:]}")
    return out.getvalue()


def profile(path: str, team: int | None = None) -> None:
    hub = unwrap(json.loads(Path(path).read_text(encoding="utf-8")))
    print(summarize_profile(hub))
    if team is None:
        return
    try:
        entry = api_get(f"entry/{team}/")
        sizes = {}
        for league in entry.get("leagues", {}).get("classic", []):
            if league.get("league_type") == "x":
                standings = api_get(f"leagues-classic/{league['id']}/standings/")["standings"]
                sizes[league["id"]] = len(standings["results"])
        print(summarize_leagues(entry, sizes))
    except (OSError, ValueError, KeyError) as e:
        raise StepFailed(f"leagues could not be read from the FPL API: {e}. Ask the person only for what is missing.")


def selling(team: int, bank: float) -> None:
    try:
        boot = api_get("bootstrap-static/")
        nxt = next((e["id"] for e in boot["events"] if e["is_next"]), None)
        event = nxt - 1 if nxt and nxt > 1 else max(e["id"] for e in boot["events"])
        picks = api_get(f"entry/{team}/event/{event}/picks/")
        transfers = api_get(f"entry/{team}/transfers/")
        rows = selling_prices([p["element_id"] for p in picks["picks"]], boot["elements"], transfers)
    except (OSError, ValueError, KeyError) as e:
        raise StepFailed(f"selling prices could not be read from the FPL API: {e}. Ask the person only for what is missing.")
    print(summarize_selling(rows, round(bank * 10)))


def fetch(team: int, league: int | None = None) -> None:
    output = run_planner(team=team, league=league)
    Path("fpl-output.txt").write_text(output, encoding="utf-8")
    print(f"fetched and scored; {len(output)} characters of tables in fpl-output.txt")


def rivals(path: str) -> None:
    raw = unwrap(json.loads(Path(path).read_text(encoding="utf-8")))
    Path("rivals.md").write_text(summarize_rivals(raw) + "\n", encoding="utf-8")
    print("wrote rivals.md")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="The deterministic FPL steps: distill, derive, fetch, format, save.")
    subs = parser.add_subparsers(dest="cmd", required=True)

    p = subs.add_parser("profile", help="distill a saved fpl_manager_hub reply")
    p.add_argument("hub")
    p.add_argument("--team", type=int, help="also list the private classic leagues via the public API")

    p = subs.add_parser("selling", help="selling prices and the true budget")
    p.add_argument("team", type=int)
    p.add_argument("--bank", type=float, required=True, help="bank in millions")

    p = subs.add_parser("scope", help="check inputs.json")
    p.add_argument("inputs", nargs="?", default="inputs.json")

    p = subs.add_parser("fetch", help="fetch and score a team (and league)")
    p.add_argument("team", type=int, nargs="?", help="defaults to inputs.json")
    p.add_argument("--league", type=int)

    p = subs.add_parser("rivals", help="format a saved rival_tracker reply")
    p.add_argument("raw")

    p = subs.add_parser("optimize", help="EV-only and league-aware squads")
    p.add_argument("team", type=int)
    p.add_argument("--budget", type=float, required=True)
    p.add_argument("--sell", required=True, help='"Name=price,..."')
    p.add_argument("--force")
    p.add_argument("--exclude")

    p = subs.add_parser("evaluate", help="inspect a 15")
    p.add_argument("team", type=int)
    p.add_argument("--budget", type=float, required=True)
    p.add_argument("--sell", required=True)
    p.add_argument("--squad", required=True, help='"15 names"')

    p = subs.add_parser("state", help="read or merge the saved plan")
    p.add_argument("team", type=int)
    p.add_argument("--write")

    args = parser.parse_args(argv)
    try:
        if args.cmd == "profile":
            profile(args.hub, args.team)
        elif args.cmd == "selling":
            selling(args.team, args.bank)
        elif args.cmd == "scope":
            inputs = json.loads(Path(args.inputs).read_text(encoding="utf-8"))
            problems = scope_problems(inputs)
            if problems:
                raise StepFailed("; ".join(problems))
            print(f"{args.inputs} is complete")
        elif args.cmd == "fetch":
            team, league = args.team, args.league
            if team is None:
                inputs = load_inputs()
                team = int(str(inputs["team"]).strip())
                league = int(str(inputs.get("league", "")).strip() or 0) or None
            fetch(team, league)
        elif args.cmd == "rivals":
            rivals(args.raw)
        elif args.cmd == "optimize":
            fpl_plan.optimize(team=args.team, budget=args.budget, sell=args.sell, force=args.force, exclude=args.exclude)
        elif args.cmd == "evaluate":
            fpl_plan.evaluate(team=args.team, budget=args.budget, sell=args.sell, squad=args.squad)
        elif args.cmd == "state":
            print(json.dumps(fpl_plan.state(args.team, write=json.loads(args.write) if args.write else None), indent=1))
    except (StepFailed, fpl_plan.PlannerError, OSError, ValueError) as e:
        print(json.dumps({"ok": False, "problems": [str(e)]}, indent=1))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
