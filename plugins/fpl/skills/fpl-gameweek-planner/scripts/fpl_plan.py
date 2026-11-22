"""FPL gameweek planner: the deterministic half of the fpl-gameweek-planner skill.

  fetch     download public FPL API data for a team (+ league rivals' picks)
  model     score every player: underlying model + realised points, per gameweek
  league    rival squads, ownership among managers ahead of you, rival XI strength
  optimize  best 15 under budget / 3-per-club, EV-only and league-aware
  evaluate  inspect a given 15: XI, bench, captain, weekly table, exposure, flags
  state     read / merge a small JSON state so a later request can resume
  run_all   fetch + model + league in one go

Each prints its tables (that is what the model reads) and raises PlannerError when it cannot go on. Plans live under
`<team>/` in `~/.fpl-planner` (override with `FPL_DATA_DIR`), so a later gameweek can resume them.

Why deterministic: these steps must give identical numbers every run, so the judgement calls (research, reconciling claims,
captaincy, chips) stay with the model.
"""
import json, math, os, random, time, unicodedata, urllib.request
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

API = "https://fantasy.premierleague.com/api"
HOME = os.environ.get("FPL_DATA_DIR") or str(Path.home() / ".fpl-planner")


def http_get_json(url: str, headers: dict | None = None):
    """GET and decode JSON. Raises OSError on a network or HTTP error."""
    request = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)
POS = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}
SLOTS = ["GK"] * 2 + ["DEF"] * 5 + ["MID"] * 5 + ["FWD"] * 3


class PlannerError(Exception):
    """The step cannot go on; the message says why and what to do."""


def fail(message):
    raise PlannerError(message)


# ----------------------------------------------------------------- helpers
def get(path, retries=2):
    """GET from the FPL API. Returns None on 403/404 (e.g. picks before a deadline)."""
    for _ in range(retries + 1):
        try:
            return http_get_json(API + path, {"User-Agent": "Mozilla/5.0"})
        except OSError:
            time.sleep(1)
    return None


def save(d, name, obj):
    with open(os.path.join(d, name), "w") as fh:
        json.dump(obj, fh, ensure_ascii=False)


def load(d, name, required=True):
    p = os.path.join(d, name)
    if not os.path.exists(p):
        if required:
            fail(f"missing {p} - run the earlier step first")
        return None
    with open(p) as fh:
        return json.load(fh)


def num(v, dflt=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return dflt


def fold(s):
    s = s.casefold()
    for a, b in (("ø", "o"), ("ß", "ss"), ("đ", "d"), ("ł", "l"), ("æ", "ae")):
        s = s.replace(a, b)
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def ptail(mean, k):
    """P(Poisson(mean) >= k)."""
    if mean <= 0:
        return 0.0
    p, s = math.exp(-mean), 0.0
    for i in range(k):
        s += p
        p *= mean / (i + 1)
    return max(0.0, 1 - s)


def availability(e):
    if e["status"] in ("i", "s", "u", "n"):
        return 0.0
    c = e["chance_of_playing_next_round"]
    if c is None:
        return 0.75 if e["status"] == "d" else 1.0
    return c / 100.0


def datadir(a):
    if getattr(a, "data", None):
        return a.data
    if not getattr(a, "team", None):
        fail("pass data (a run's directory) or team (an FPL team id)")
    base = f"{HOME}/{a.team}"
    latest = sorted([x for x in os.listdir(base) if x.startswith("gw")], key=lambda x: int(x[2:])) if os.path.isdir(base) else []
    if not latest:
        fail(f"no data under {base}; run fetch first")
    return f"{base}/{latest[-1]}/data"


# ----------------------------------------------------------------- fetch
def cmd_fetch(a):
    boot = get("/bootstrap-static/")
    if not boot:
        fail("could not reach the FPL API")
    nxt = next((e["id"] for e in boot["events"] if e["is_next"]), None)
    if nxt is None:
        fail("no upcoming gameweek (season finished?)")
    d = a.out or f"{HOME}/{a.team}/gw{nxt}/data"
    os.makedirs(d, exist_ok=True)
    for fn in os.listdir(d):  # drop picks/standings from earlier runs so rivals never mix across fetches
        if fn.startswith("picks_") or fn in ("standings.json", "overlay.json"):
            os.remove(os.path.join(d, fn))
    save(d, "boot.json", boot)
    save(d, "fix.json", get("/fixtures/") or [])
    save(d, "entry.json", get(f"/entry/{a.team}/") or {})
    last = nxt - 1
    ids = [a.team]
    if a.league:
        std = get(f"/leagues-classic/{a.league}/standings/")
        if std:
            save(d, "standings.json", std)
            res = std["standings"]["results"]
            me = next((r for r in res if r["entry"] == a.team), None)
            if me:
                above = [r for r in res if r["rank"] < me["rank"]][-a.ahead:]
                below = [r for r in res if r["rank"] > me["rank"]][:a.below]
                ids += [r["entry"] for r in above + below]
            else:
                print("note: your team is not on the first page of the league standings; only your own picks fetched")
    got = 0
    for i in ids:
        j = get(f"/entry/{i}/event/{last}/picks/") if last >= 1 else None
        if j:
            save(d, f"picks_{i}.json", j)
            got += 1
    dl = next(e["deadline_time"] for e in boot["events"] if e["id"] == nxt)
    print(f"fetched -> {d}\nnext gameweek GW{nxt}, deadline {dl} (UTC)\npicks for GW{last}: {got}/{len(ids)} managers")
    if a.league and not os.path.exists(f"{d}/standings.json"):
        print("warning: league standings not available (private league or wrong id)")


# ----------------------------------------------------------------- model
def cmd_model(a):
    d = datadir(a)
    boot, fix = load(d, "boot.json"), load(d, "fix.json")
    nxt = next((e["id"] for e in boot["events"] if e["is_next"]), None)
    if nxt is None:
        fail("no upcoming gameweek")
    gws = list(range(nxt, min(38, nxt + a.horizon - 1) + 1))
    teams = {t["id"]: t["short_name"] for t in boot["teams"]}
    els = boot["elements"]
    gp = defaultdict(int)
    for f in fix:
        if f.get("finished"):
            gp[f["team_h"]] += 1
            gp[f["team_a"]] += 1
    # Team strength from player data (the API's own strength_* fields are unreliable/zeroed).
    XGF, XGA = {}, {}
    for tid in teams:
        pl = [e for e in els if e["team"] == tid]
        XGF[tid] = sum(num(e["expected_goals"]) for e in pl) / gp[tid] if gp[tid] else None
        gks = sorted([e for e in pl if e["element_type"] == 1], key=lambda e: -e["minutes"])
        XGA[tid] = num(gks[0]["expected_goals_conceded_per_90"]) if gks and gks[0]["minutes"] > 0 else None
    vf = [v for v in XGF.values() if v]
    va = [v for v in XGA.values() if v]
    mF, mA = (sum(vf) / len(vf) if vf else 1.0), (sum(va) / len(va) if va else 1.0)
    facF = lambda t: (XGF[t] / mF) if XGF[t] else 1.0   # >1 = stronger attack
    facA = lambda t: (XGA[t] / mA) if XGA[t] else 1.0   # >1 = leakier defence
    fx = defaultdict(lambda: defaultdict(list))
    for f in fix:
        g = f.get("event")
        if g in gws:
            fx[f["team_h"]][g].append((f["team_a"], True))
            fx[f["team_a"]][g].append((f["team_h"], False))
    w = a.blend
    out = []
    for e in els:
        pos, mins, starts = e["element_type"], e["minutes"], e["starts"] or 0
        xg, xa = num(e["expected_goals_per_90"]), num(e["expected_assists_per_90"])
        xgc, dc = num(e["expected_goals_conceded_per_90"]), num(e["defensive_contribution_per_90"])
        bonus, saves = num(e["bonus"]) / max(1, starts), num(e.get("saves_per_90"))
        ppg = num(e["points_per_game"])           # points per appearance
        tg = gp[e["team"]] or max(1, nxt - 1)
        pstart = min(1.0, mins / (tg * 90.0))
        av = availability(e)
        xps, es, labels = [], [], []
        for g in gws:
            fl = fx[e["team"]].get(g, [])
            xp = 0.0
            for opp, home in fl:
                atk = facA(opp) * (1.1 if home else 0.9)   # easier to score vs a leaky team, at home
                dfn = facF(opp) * (0.9 if home else 1.1)   # harder to keep a clean sheet vs a strong attack
                gxg, gxa, gxgc = xg * atk, xa * atk, xgc * dfn
                cs = math.exp(-gxgc)
                if pos == 1:
                    pts = 2 + 4 * cs - 0.5 * gxgc + saves / 3 + bonus
                elif pos == 2:
                    pts = 2 + 6 * gxg + 3 * gxa + 4 * cs - 0.5 * gxgc + 2 * ptail(dc, 10) + bonus
                elif pos == 3:
                    pts = 2 + 5 * gxg + 3 * gxa + cs + 2 * ptail(dc, 12) + bonus
                else:
                    pts = 2 + 4 * gxg + 3 * gxa + 2 * ptail(dc, 12) + bonus
                xp += pts
            xp *= pstart
            xps.append(round(xp, 3))
            es.append(round(av * (w * xp + (1 - w) * ppg * pstart * len(fl)), 3))
            labels.append("/".join(("v " if h else "@ ") + teams[o] for o, h in fl) or "BLANK")
        out.append(dict(
            id=e["id"], name=e["web_name"], full=f'{e["first_name"]} {e["second_name"]}', team=teams[e["team"]], pos=POS[pos],
            price=e["now_cost"] / 10, own=num(e["selected_by_percent"]), status=e["status"], news=e["news"],
            cop=e["chance_of_playing_next_round"], mins=mins, starts=starts, mshare=round(pstart, 2), pts=e["total_points"],
            ppg=ppg, form=num(e["form"]), xgi90=num(e["expected_goal_involvements_per_90"]), xgc90=xgc, dc90=dc,
            yellows=e["yellow_cards"], pen=e["penalties_order"], corner=e["corners_and_indirect_freekicks_order"],
            fk=e["direct_freekicks_order"], tin=e["transfers_in_event"], tout=e["transfers_out_event"],
            avail=av, xp=xps, e=es, E=round(sum(es), 3), e1=es[0] if es else 0.0, fixtures=labels))
    save(d, "players.json", out)
    dl = next(e["deadline_time"] for e in boot["events"] if e["id"] == nxt)
    save(d, "meta.json", dict(nxt=nxt, gws=gws, deadline=dl, blend=w, horizon=a.horizon))
    print(f"model -> {d}/players.json ({len(out)} players), gameweeks {gws}, blend {w} underlying / {1 - w} realised")
    cnt = defaultdict(lambda: defaultdict(int))
    for f in fix:
        g = f.get("event")
        if g and g >= nxt:
            cnt[g][f["team_h"]] += 1
            cnt[g][f["team_a"]] += 1
    dgw = [f"GW{g}: {','.join(teams[t] for t, c in cnt[g].items() if c >= 2)}" for g in sorted(cnt) if any(c >= 2 for c in cnt[g].values())]
    bgw = [f"GW{g}: {len([t for t in teams if cnt[g].get(t, 0) == 0])} teams" for g in sorted(cnt) if any(cnt[g].get(t, 0) == 0 for t in teams)]
    print("scheduled double gameweeks:", "; ".join(dgw) or "none yet", "| blank gameweeks:", "; ".join(bgw) or "none yet", "(unscheduled fixtures are not counted)")
    pool = [p for p in out if p["mins"] >= 250 and p["E"] > 0]
    for pos in ("GK", "DEF", "MID", "FWD"):
        top = sorted([p for p in pool if p["pos"] == pos], key=lambda p: -p["E"])[: a.top]
        print(f"-- top {pos} by E (horizon score)")
        for i, p in enumerate(top, 1):
            print(f'  {i:2}. {p["name"]:14}{p["team"]} £{p["price"]:4.1f} E={p["E"]:5.1f} e1={p["e1"]:4.1f} ppg={p["ppg"]:4.1f} own={p["own"]:4.1f}%  {" ".join(p["fixtures"][:3])}')


# ----------------------------------------------------------------- league
def cmd_league(a):
    d = datadir(a)
    players = {p["id"]: p for p in load(d, "players.json")}
    meta = load(d, "meta.json")
    std = load(d, "standings.json", required=False)
    names = {r["entry"]: r for r in (std["standings"]["results"] if std else [])}
    my_total = names.get(a.team, {}).get("total")
    rivals = {}
    for fn in os.listdir(d):
        if fn.startswith("picks_") and fn.endswith(".json"):
            i = int(fn[6:-5])
            if i != a.team:
                rivals[i] = load(d, fn)
    own_all, own_ahead, caps = defaultdict(int), defaultdict(int), defaultdict(int)
    ahead = [i for i in rivals if my_total is not None and names.get(i, {}).get("total", 0) > my_total]
    summary = []
    for i, j in rivals.items():
        picks = j["picks"]
        xi = [p for p in picks if p["position"] <= 11]
        cap = next((p for p in picks if p["is_captain"]), None)
        E = sum(players[p["element"]]["E"] for p in xi) + (players[cap["element"]]["E"] * (cap["multiplier"] - 1) if cap else 0)
        dead = [players[p["element"]]["name"] for p in xi if players[p["element"]]["avail"] < 0.5]
        eh = j["entry_history"]
        for p in picks:
            own_all[p["element"]] += 1
            if i in ahead:
                own_ahead[p["element"]] += 1
        if cap:
            caps[cap["element"]] += 1
        r = names.get(i, {})
        summary.append(dict(entry=i, manager=r.get("player_name", str(i)), team=r.get("entry_name", ""), rank=r.get("rank"), total=r.get("total"),
                            ahead=i in ahead, chip=j.get("active_chip"), gw_points=eh["points"], hit=eh["event_transfers_cost"], bank=eh["bank"] / 10,
                            captain=players[cap["element"]]["name"] if cap else None, xi_E=round(E, 1), dead_starters=dead))
    summary.sort(key=lambda r: (r["rank"] or 99))
    mine = load(d, f"picks_{a.team}.json", required=False)
    res = dict(my_total=my_total, n_all=len(rivals), n_ahead=len(ahead), summary=summary,
               own_all={str(k): v for k, v in own_all.items()}, own_ahead={str(k): v for k, v in own_ahead.items()},
               captains={str(k): v for k, v in caps.items()}, my_chip=mine.get("active_chip") if mine else None,
               my_entry_history=mine["entry_history"] if mine else None, my_picks=[p["element"] for p in mine["picks"]] if mine else [])
    save(d, "overlay.json", res)
    print(f"league overlay -> {d}/overlay.json  rivals={len(rivals)} ahead of you={len(ahead)}")
    print(f'{"rank":>4} {"manager":16}{"total":>6} {"chip(last GW)":14}{"hit":>4} {"captain":12}{"XI-E":>6}  dead/injured starters')
    for r in summary:
        print(f'{r["rank"]!s:>4} {r["manager"][:15]:16}{r["total"]!s:>6} {r["chip"] or "-":14}{r["hit"]:>4} {r["captain"] or "-":12}{r["xi_E"]:>6}  {", ".join(r["dead_starters"]) or "-"}')
    print("-- ownership among managers ahead (n=%d) / all rivals (n=%d): most owned" % (len(ahead), len(rivals)))
    for k in sorted(own_all, key=lambda k: -own_ahead.get(k, 0) - 0.01 * own_all[k])[: a.top]:
        print(f'   {players[k]["name"]:14}{players[k]["team"]} ahead={own_ahead.get(k, 0)}/{len(ahead)} all={own_all[k]}/{len(rivals)} captained={caps.get(k, 0)} E={players[k]["E"]:.1f}')


# ----------------------------------------------------------------- shared loading for optimize / evaluate
def load_all(a):
    d = datadir(a)
    players = {p["id"]: p for p in load(d, "players.json")}
    meta = load(d, "meta.json")
    ov = load(d, "overlay.json", required=False) or {}
    na, nl = ov.get("n_ahead", 0), ov.get("n_all", 0)
    for p in players.values():
        k = str(p["id"])
        p["ahead"] = ov.get("own_ahead", {}).get(k, 0)
        p["all"] = ov.get("own_all", {}).get(k, 0)
        p["L"] = round(p["E"] * (1 + a.premium * (1 - p["ahead"] / na)) if na else p["E"], 3)
    return d, players, meta, ov


def resolve(players, tokens):
    """'Name', 'Name:TEAM' or numeric id -> player id. Exits with the candidates if ambiguous."""
    ids = []
    for t in [x.strip() for x in tokens.split(",") if x.strip()]:
        if t.isdigit() and int(t) in players:
            ids.append(int(t))
            continue
        nm, _, tm = t.partition(":")
        m = [p for p in players.values() if fold(p["name"]) == fold(nm) and (not tm or p["team"].upper() == tm.upper())]
        if not m:
            m = [p for p in players.values() if fold(nm) in fold(p["name"]) and (not tm or p["team"].upper() == tm.upper())]
        m = [p for p in m if p["mins"] > 0 or p["pos"] == "GK"] or m
        if len(m) > 1:
            exact = [p for p in m if fold(p["name"]) == fold(nm)]
            m = exact or m
        if len(m) != 1:
            fail(f"cannot resolve '{t}': " + (", ".join(f'{p["name"]}:{p["team"]}({p["pos"]})' for p in m[:8]) or "no match") + " - use Name:TEAM")
        ids.append(m[0]["id"])
    return ids


def prices(players, sell, owned):
    pr = {pid: p["price"] for pid, p in players.items()}
    for tok in [x for x in (sell or "").split(",") if x.strip()]:
        nm, _, val = tok.rpartition("=")
        pid = resolve(players, nm)[0]
        pr[pid] = float(val)
    return pr


def best_xi(sq, players, key):
    g = sorted([x for x in sq if players[x]["pos"] == "GK"], key=lambda x: -players[x][key])
    o = {p: sorted([x for x in sq if players[x]["pos"] == p], key=lambda x: -players[x][key]) for p in ("DEF", "MID", "FWD")}
    best = (-1, None, None)
    for dd in range(3, 6):
        for ff in range(1, 4):
            m = 10 - dd - ff
            if 2 <= m <= 5 and len(o["DEF"]) >= dd and len(o["MID"]) >= m and len(o["FWD"]) >= ff and g:
                xi = [g[0]] + o["DEF"][:dd] + o["MID"][:m] + o["FWD"][:ff]
                v = sum(players[x][key] for x in xi)
                if v > best[0]:
                    best = (v, xi, (dd, m, ff))
    return best


# ----------------------------------------------------------------- optimize
def cmd_optimize(a):
    d, players, meta, ov = load_all(a)
    eh = ov.get("my_entry_history")
    budget = a.budget if a.budget else ((eh["value"] + eh["bank"]) / 10 if eh else None)
    if budget is None:
        fail("pass budget (the app's total: squad selling value + bank)")
    if not a.budget:
        print(f"note: budget {budget} comes from the API's team value + bank; the app uses SELLING prices, so pass budget from the app/screenshot for accuracy")
    pr = prices(players, a.sell, None)
    force = set(resolve(players, a.force)) if a.force else set()
    exclude = set(resolve(players, a.exclude)) if a.exclude else set()
    cand = {pos: [p["id"] for p in players.values() if p["pos"] == pos and p["id"] not in exclude and p["avail"] >= 0.75
                  and (p["mins"] >= a.min_minutes or (pr[p["id"]] <= a.fodder and p["status"] == "a"))] for pos in POS.values()}
    for f in force:
        if f not in cand[players[f]["pos"]]:
            cand[players[f]["pos"]].append(f)

    def ok(sq):
        if sum(pr[x] for x in sq) > budget + 1e-9:
            return False
        c = defaultdict(int)
        for x in sq:
            c[players[x]["team"]] += 1
        return max(c.values()) <= a.max_per_club

    def val(sq, key):
        v, xi, _ = best_xi(sq, players, key)
        return v + a.bench_weight * sum(players[x][key] for x in sq if x not in xi)

    def start():
        """Cheapest legal squad (respecting the club limit) with forced players placed in; annealing improves it."""
        sq = [None] * 15
        cnt = defaultdict(int)
        for f in force:
            i = next(i for i, s in enumerate(SLOTS) if s == players[f]["pos"] and sq[i] is None)
            sq[i] = f
            cnt[players[f]["team"]] += 1
        for i, pos in enumerate(SLOTS):
            if sq[i] is None:
                pool = sorted([x for x in cand[pos] if x not in sq and cnt[players[x]["team"]] < a.max_per_club], key=lambda x: pr[x])
                sq[i] = pool[0]
                cnt[players[pool[0]]["team"]] += 1
        return sq

    def anneal(key, init, iters):
        cur = list(init)
        if not ok(cur):
            fail("forced players + cheapest fillers exceed the budget / club limit")
        cv = val(cur, key)
        best, bv = list(cur), cv
        for i in range(iters):
            T = 1.2 * (1 - i / iters) + 0.01
            k = random.randrange(15)
            if cur[k] in force:
                continue
            c = random.choice(cand[SLOTS[k]])
            if c in cur:
                continue
            new = list(cur)
            new[k] = c
            if not ok(new):
                continue
            v = val(new, key)
            if v >= cv or random.random() < math.exp((v - cv) / T):
                cur, cv = new, v
                if v > bv:
                    best, bv = list(new), v
        return best, bv

    random.seed(a.seed)
    results = {}
    for key, title in (("E", "EV-only (E)"), ("L", f"league-aware (E with +{int(a.premium * 100)}% premium for players none of the managers ahead own)")):
        runs = sorted([anneal(key, start(), a.iters) for _ in range(a.restarts)], key=lambda x: -x[1])
        sq = runs[0][0]
        results[key] = sq
        _, xi, f = best_xi(sq, players, "e1")
        print(f"\n== {title}: objective {runs[0][1]:.1f}, cost {sum(pr[x] for x in sq):.1f} / budget {budget}")
        for pos in POS.values():
            row = sorted([x for x in sq if players[x]["pos"] == pos], key=lambda x: -players[x]["E"])
            print(f"   {pos:3} " + ", ".join(f'{players[x]["name"]}({players[x]["team"]} £{pr[x]:.1f} E={players[x]["E"]:.1f} ahead={players[x]["ahead"]}/{ov.get("n_ahead", 0)}){"" if x in xi else "*"}' for x in row))
        print(f"   first-GW XI {f[0]}-{f[1]}-{f[2]} (* = bench)")
    save(d, "plan.json", {k: [players[x]["name"] + ":" + players[x]["team"] for x in v] for k, v in results.items()})
    print(f"\nplan -> {d}/plan.json   (the optimum is only a starting point: if it beats your squad by <~2% it is inside the model's noise)")


# ----------------------------------------------------------------- evaluate
def cmd_evaluate(a):
    d, players, meta, ov = load_all(a)
    if a.squad:
        sq = resolve(players, a.squad)
    else:
        sq = ov.get("my_picks") or fail("pass squad or fetch your picks first")
    if len(sq) != 15:
        fail(f"squad has {len(sq)} players, need 15")
    pr = prices(players, a.sell, None)
    na, nl, gws = ov.get("n_ahead", 0), ov.get("n_all", 0), meta["gws"]
    cost = sum(pr[x] for x in sq)
    cl = defaultdict(int)
    for x in sq:
        cl[players[x]["team"]] += 1
    print(f"squad cost {cost:.1f}" + (f" vs budget {a.budget} (spare {a.budget - cost:+.1f})" if a.budget else "") + "  clubs: " + ", ".join(f"{k}x{v}" for k, v in sorted(cl.items(), key=lambda kv: -kv[1])))
    v, xi, f = best_xi(sq, players, "e1")
    print(f"\nper-gameweek score (e) and fixtures; gameweeks {gws}")
    print(f'{"player":13}{"pos":4}{"team":5}{"£":>5} ' + " ".join(f"GW{g:<2}      " for g in gws) + "    E  ahead/all  flags")
    for x in sorted(sq, key=lambda x: (list(POS.values()).index(players[x]["pos"]), -players[x]["E"])):
        p = players[x]
        flags = []
        if p["avail"] < 1:
            flags.append(f'{p["status"]}/{p["cop"]}')
        if p["mshare"] < 0.85:
            flags.append(f'mins {p["mshare"]}')
        if p["yellows"] >= 3:
            flags.append(f'{p["yellows"]}YC')
        if p["tout"] - p["tin"] > 200000:
            flags.append("price-fall?")
        print(f'{p["name"]:13}{p["pos"]:4}{p["team"]:5}{pr[x]:5.1f} ' + " ".join(f'{p["e"][i]:4.1f}{p["fixtures"][i][:7]:>7}' for i in range(len(gws))) + f' {p["E"]:5.1f}  {p["ahead"]}/{na} {p["all"]}/{nl}  {" ".join(flags)}')
    print(f"\nbest first-GW XI by e1: formation {f[0]}-{f[1]}-{f[2]}  score {v:.1f}")
    print("  XI:", ", ".join(players[x]["name"] for x in xi))
    print("  bench:", ", ".join(players[x]["name"] for x in sq if x not in xi))
    alt = []
    for dd in range(3, 6):
        for ff in range(1, 4):
            m = 10 - dd - ff
            if 2 <= m <= 5:
                o = {p: sorted([x for x in sq if players[x]["pos"] == p], key=lambda x: -players[x]["e1"]) for p in ("DEF", "MID", "FWD")}
                g_ = sorted([x for x in sq if players[x]["pos"] == "GK"], key=lambda x: -players[x]["e1"])[0]
                if len(o["DEF"]) >= dd and len(o["MID"]) >= m and len(o["FWD"]) >= ff:
                    alt.append((sum(players[x]["e1"] for x in [g_] + o["DEF"][:dd] + o["MID"][:m] + o["FWD"][:ff]), f"{dd}-{m}-{ff}"))
    print("  formations:", ", ".join(f"{n} {s:.1f}" for s, n in sorted(alt, reverse=True)[:5]), "(near-ties: break them with the league overlay / correlation)")
    cap = sorted([x for x in sq if players[x]["pos"] in ("MID", "FWD")], key=lambda x: -players[x]["e1"])[:6]
    top = players[cap[0]]["e1"]
    print("\ncaptain candidates (e1, expected cost vs best, managers ahead owning, rivals captaining):")
    for x in cap:
        p = players[x]
        print(f'   {p["name"]:13}e1={p["e1"]:4.1f} cost={top - p["e1"]:4.1f}  ahead={p["ahead"]}/{na}  captained by {ov.get("captains", {}).get(str(x), 0)}/{nl}  pen={p["pen"]}')
    thr = 0.8 * sorted([players[x]["E"] for x in xi])[0]
    exp = [p for p in players.values() if p["id"] not in sq and p["avail"] >= 0.75 and p["E"] >= thr and na and p["ahead"] / na >= 0.5]
    print("\nexposure: strong players you do NOT own that >=half the managers ahead own:",
          ", ".join(f'{p["name"]}({p["pos"]} {p["ahead"]}/{na}, E={p["E"]:.1f})' for p in sorted(exp, key=lambda p: -p["E"])) or "none")
    if ov.get("summary"):
        capE = players[cap[0]]["E"]
        mine_xi = best_xi(sq, players, "E")[1]
        # the captain counts twice only when he is actually in the XI
        my_xi_E = sum(players[x]["E"] for x in mine_xi) + (capE if cap[0] in mine_xi else 0)
        print("\nmodel edge over rivals' last-GW squads, horizon total (OPTIMISTIC: your squad is chosen by this same model and rivals will fix dead slots - direction only):")
        for r in ov["summary"]:
            print(f'   vs {r["manager"][:15]:16} rank {r["rank"]}: rival {r["xi_E"]:.1f}  you {my_xi_E:.1f}  edge {my_xi_E - r["xi_E"]:+.1f}')


# ----------------------------------------------------------------- public API
def state(team, write=None):
    """The saved plan for the team (an empty dict when there is none); `write` (a dict) is merged into it first."""
    os.makedirs(f"{HOME}/{team}", exist_ok=True)
    p = f"{HOME}/{team}/state.json"
    cur = json.load(open(p)) if os.path.exists(p) else {}
    if write:
        cur.update(write)
        cur["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
        json.dump(cur, open(p, "w"), indent=1, ensure_ascii=False)
    return cur


def fetch(team, league=None, out=None, ahead=8, below=4):
    cmd_fetch(SimpleNamespace(team=team, league=league, out=out, ahead=ahead, below=below, data=None))


def model(team=None, data=None, horizon=5, blend=0.5, top=12):
    cmd_model(SimpleNamespace(team=team, data=data, horizon=horizon, blend=blend, top=top))


def league(team=None, data=None, top=20):
    cmd_league(SimpleNamespace(team=team, data=data, top=top))


def run_all(team, league=None, out=None, ahead=8, below=4, horizon=5, blend=0.5):
    """fetch + model + league, printing the tables the later steps read."""
    a = SimpleNamespace(team=team, league=league, out=out, ahead=ahead, below=below, horizon=horizon, blend=blend, data=None, top=8)
    cmd_fetch(a)
    a.data = a.out
    cmd_model(a)
    cmd_league(a)


def optimize(team=None, data=None, budget=None, sell=None, premium=0.10, force=None, exclude=None, max_per_club=3,
             min_minutes=250, fodder=4.5, bench_weight=0.12, iters=30000, restarts=4, seed=3):
    """`sell` is 'Haaland=15.6,Raya=6.1'; `force` and `exclude` are comma lists of names."""
    cmd_optimize(SimpleNamespace(team=team, data=data, budget=budget, sell=sell, premium=premium, force=force, exclude=exclude,
                                 max_per_club=max_per_club, min_minutes=min_minutes, fodder=fodder, bench_weight=bench_weight,
                                 iters=iters, restarts=restarts, seed=seed))


def evaluate(team=None, data=None, budget=None, sell=None, premium=0.10, squad=None):
    """`squad` is a comma list of 15 names ('Name' or 'Name:TEAM'); the default is the team's last-gameweek picks."""
    cmd_evaluate(SimpleNamespace(team=team, data=data, budget=budget, sell=sell, premium=premium, squad=squad))
