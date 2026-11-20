"""The mechanical part of planning a trip: rank candidates by the person's preferences, check an itinerary, and date the
pre-trip reminders. Each takes its input as the data itself or as the path of a JSON file, and returns one dict; the model
still chooses the places and the shape of the day.

  python3 scripts/travelplan.py rank candidates.json [preferences.json] [--top 15]
  python3 scripts/travelplan.py check plan.json [preferences.json]
  python3 scripts/travelplan.py reminders brief.json [preferences.json]

`problems` means fix the input; `warnings` means the plan is usable but something was skipped or is unverified.
"""

from __future__ import annotations

import argparse
import json
import math
import uuid
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

PACE = ("relaxed", "balanced", "packed")
BUDGET = ("shoestring", "mid", "comfort", "luxury")
MOBILITY = ("full", "limited", "wheelchair")
BUDGET_LEVEL = {"shoestring": 1, "mid": 2, "comfort": 3, "luxury": 4}
MAX_STOPS = {"relaxed": 4, "balanced": 6, "packed": 8}
PACE_FACTOR = {"relaxed": 1.0, "balanced": 1.5, "packed": 2.0}
TOPICS = {
    "food": ("restaurant", "cafe", "bakery", "market", "food", "coffee", "bistro"),
    "culture": ("museum", "gallery", "historical", "landmark", "monument", "theater", "church"),
    "history": ("historical", "monument", "museum", "castle", "ruins", "heritage"),
    "nature": ("park", "garden", "hiking", "beach", "nature", "trail", "viewpoint"),
    "hiking": ("hiking", "trail", "mountain", "nature", "park"),
    "nightlife": ("bar", "night_club", "live_music", "club", "pub"),
    "shopping": ("shopping", "store", "mall", "market", "boutique"),
    "relaxation": ("spa", "beach", "park", "cafe", "garden"),
    "family": ("zoo", "aquarium", "amusement", "playground", "park"),
    "beach": ("beach", "coast", "seaside"),
    "architecture": ("architecture", "cathedral", "church", "monument", "building"),
    "art": ("art_gallery", "museum", "gallery"),
    "wildlife": ("zoo", "aquarium", "wildlife", "nature"),
}
AVOID = ("crowds", "early_mornings", "long_walks", "tourist_traps", "museums", "nightlife", "shopping")
PRIORITIES = tuple(TOPICS) + ("minimize_transit", "comfort")

DEFAULT_PREFS = {
    "pace": "balanced",
    "budget": "mid",
    "interests": [],
    "priorities": [],
    "avoid": [],
    "mobility": "full",
    "travelers": {"adults": 2, "children": 0, "infants": 0},
    "dietary": [],
    "home_airport": "",
    "currency": "USD",
    "time_zone": "UTC",
    "must_see": [],
    "never": [],
    "max_daily_travel_minutes": 90,
    "day_start": "09:00",
    "day_end": "21:00",
}


def normalize_prefs(raw: dict | None) -> tuple[dict, list[str]]:
    """Defaults, types and limits; every problem names the field."""
    problems: list[str] = []
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        return dict(DEFAULT_PREFS), ["preferences must be a JSON object"]
    prefs = json.loads(json.dumps(DEFAULT_PREFS))
    for key in ("interests", "priorities", "avoid", "dietary", "must_see", "never"):
        value = raw.get(key)
        if value is None:
            continue
        if not isinstance(value, list) or any(not isinstance(v, str) for v in value):
            problems.append(f"preferences.{key} must be a list of words")
        else:
            prefs[key] = [v.strip() for v in value if v.strip()]
    for key, allowed in (("pace", PACE), ("budget", BUDGET), ("mobility", MOBILITY)):
        value = raw.get(key, prefs[key])
        if value not in allowed:
            problems.append(f"preferences.{key} must be one of {', '.join(allowed)}")
        else:
            prefs[key] = value
    unknown = [p for p in prefs["priorities"] if p not in PRIORITIES]
    if unknown:
        problems.append(f"preferences.priorities has unknown {unknown}; use {', '.join(PRIORITIES)}")
    unknown = [a for a in prefs["avoid"] if a not in AVOID]
    if unknown:
        problems.append(f"preferences.avoid has unknown {unknown}; use {', '.join(AVOID)}")

    travelers = raw.get("travelers", prefs["travelers"])
    if isinstance(travelers, int) and not isinstance(travelers, bool):
        if travelers < 1:
            problems.append("preferences.travelers must be at least 1")
        else:
            prefs["travelers"] = {"adults": travelers, "children": 0, "infants": 0}
    elif isinstance(travelers, dict):
        people = {"adults": 1, "children": 0, "infants": 0}
        for key in people:
            n = travelers.get(key, people[key])
            if not isinstance(n, int) or isinstance(n, bool) or n < 0:
                problems.append(f"preferences.travelers.{key} must be a whole number, 0 or more")
            else:
                people[key] = n
        if sum(people.values()) < 1:
            problems.append("preferences.travelers must add up to at least 1")
        prefs["travelers"] = people
    else:
        problems.append("preferences.travelers must be a number or {adults, children, infants}")

    for key, low, high, fallback in (("max_daily_travel_minutes", 0, 600, 90),):
        value = raw.get(key, fallback)
        if not isinstance(value, int) or isinstance(value, bool) or not low <= value <= high:
            problems.append(f"preferences.{key} must be {low}-{high}")
        else:
            prefs[key] = value
    for key in ("day_start", "day_end"):
        value = raw.get(key, DEFAULT_PREFS[key])
        if _hhmm(value) is None:
            problems.append(f"preferences.{key} must be HH:MM")
        else:
            prefs[key] = value
    for key in ("home_airport", "currency", "time_zone"):
        value = raw.get(key, DEFAULT_PREFS[key])
        if not isinstance(value, str):
            problems.append(f"preferences.{key} must be text")
        else:
            prefs[key] = value.strip()
    if prefs["time_zone"]:
        try:
            ZoneInfo(prefs["time_zone"])
        except Exception:
            problems.append(f"preferences.time_zone {prefs['time_zone']!r} is not an IANA zone")
    return prefs, problems


def _hhmm(text: str) -> time | None:
    try:
        return datetime.strptime(str(text), "%H:%M").time()
    except (ValueError, TypeError):
        return None


def _minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def _clock(day: date, minutes: int) -> datetime:
    return datetime.combine(day, time.min) + timedelta(minutes=minutes)


def _hay(candidate: dict) -> str:
    parts = [str(candidate.get("name", ""))]
    for key in ("types", "tags"):
        value = candidate.get(key) or []
        if isinstance(value, list):
            parts.extend(str(v) for v in value)
        elif isinstance(value, str):
            parts.append(value)
    return " ".join(parts).lower()


def _contains(hay: str, term: str) -> bool:
    """A plain term or its singular, so a never-list entry like "nightclubs" still matches "Nightclub X"."""
    term = term.lower().strip()
    return bool(term) and (term in hay or (term.endswith("s") and len(term) > 3 and term[:-1] in hay))


def _matches(hay: str, topic: str) -> bool:
    return any(word in hay for word in TOPICS.get(topic, (topic,)))


def load(source):
    """The data itself, or the JSON in the file at that path."""
    if isinstance(source, (str, bytes)) or hasattr(source, "__fspath__"):
        with open(source, encoding="utf-8") as f:
            return json.load(f)
    return source


def rank(candidates: list | str, prefs: dict | str | None = None, top: int = 15) -> dict:
    """A transparent shortlist: hard never-list excluded, must-sees first, then interests/priorities, rating, price and
    distance. The model still chooses for fit, opening hours and the shape of the day."""
    candidates, prefs = load(candidates), load(prefs or {})
    prefs, problems = normalize_prefs(prefs)
    if not isinstance(candidates, list):
        return {"ok": False, "problems": problems + ["candidates must be a list"], "ranking": []}
    if top < 1:
        problems.append("top must be at least 1")
        top = 15

    ranked = []
    for c in candidates:
        if not isinstance(c, dict) or not str(c.get("name") or "").strip():
            continue
        hay = _hay(c)
        if any(_contains(hay, n) for n in prefs["never"] if n):
            continue
        score = 0.0
        reasons: list[str] = []
        for must in prefs["must_see"]:
            if _contains(hay, must):
                score += 100
                reasons.append("must-see")
                break
        for interest in prefs["interests"]:
            if _matches(hay, interest):
                score += 6
                reasons.append(f"interest: {interest}")
        for priority in prefs["priorities"]:
            if priority in TOPICS and _matches(hay, priority):
                score += 10
                reasons.append(f"priority: {priority}")

        rating = c.get("rating")
        if isinstance(rating, (int, float)) and not isinstance(rating, bool):
            score += max(0.0, float(rating) - 4.0) * 10
            if rating >= 4.5:
                reasons.append(f"rated {rating}")
                if "comfort" in prefs["priorities"]:
                    score += 2
        count = c.get("ratings_count")
        if isinstance(count, (int, float)) and not isinstance(count, bool) and count > 0:
            score += min(5.0, math.log10(float(count) + 1))
            if count > 5000:
                if "crowds" in prefs["avoid"]:
                    score -= 8
                    reasons.append("crowded")
                else:
                    reasons.append("popular")
        level = c.get("price_level")
        budget = BUDGET_LEVEL[prefs["budget"]]
        if isinstance(level, int) and not isinstance(level, bool):
            if level > budget:
                score -= (level - budget) * 6
                reasons.append("over budget")
            else:
                score += 2
                if "comfort" in prefs["priorities"] and level >= 3:
                    score += 4
                    reasons.append("comfort")
        distance = c.get("distance_km")
        if isinstance(distance, (int, float)) and not isinstance(distance, bool) and distance >= 0:
            factor = PACE_FACTOR[prefs["pace"]]
            if "minimize_transit" in prefs["priorities"]:
                factor *= 2
            if "long_walks" in prefs["avoid"] or prefs["mobility"] != "full":
                factor *= 2
            score -= float(distance) * factor
            if distance > 10:
                reasons.append(f"{distance:g} km away")
        if "tourist_traps" in prefs["avoid"] and "tourist" in hay:
            score -= 10
            reasons.append("tourist trap")
        for item, topic in (("museums", "culture"), ("nightlife", "nightlife"), ("shopping", "shopping")):
            if item in prefs["avoid"] and _matches(hay, topic):
                score -= 10
                reasons.append(f"avoid: {item}")
        ranked.append({
            "name": str(c["name"]).strip(),
            "score": round(score, 1),
            "reasons": reasons or ["no preference signals"],
            "candidate": c,
        })
    ranked.sort(key=lambda r: (-r["score"], r["name"].lower()))
    return {"ok": not problems, "problems": problems, "ranking": ranked[:top]}


def check(plan: dict | str, prefs: dict | str | None = None) -> dict:
    """Every problem in a day-by-day plan, each naming the day and stop."""
    plan, prefs = load(plan), load(prefs or {})
    prefs, problems = normalize_prefs(prefs)
    if not isinstance(plan, dict):
        return {"ok": False, "problems": problems + ["plan must be a JSON object"]}
    start = _date(plan.get("start"), "start", problems)
    end = _date(plan.get("end"), "end", problems)
    if start and end and end < start:
        problems.append(f"end {end} is before start {start}")
    currency = str(plan.get("currency") or prefs["currency"]).upper()
    travelers = _traveler_count(plan.get("travelers", prefs["travelers"]), problems)

    days = plan.get("days") or []
    if not isinstance(days, list) or not days:
        problems.append("the plan has no days")
        days = []
    seen_days: set[date] = set()
    for i, day in enumerate(days):
        where = f"days[{i}]"
        if not isinstance(day, dict):
            problems.append(f"{where}: must be an object")
            continue
        d = _date(day.get("date"), f"{where}.date", problems)
        if d:
            where = f"day {d}"
            if start and d < start or end and d > end:
                problems.append(f"{where}: outside the trip ({start} to {end})")
            if d in seen_days:
                problems.append(f"{where}: appears twice")
            seen_days.add(d)
        day_start = _hhmm(day.get("start") or prefs["day_start"])
        day_end = _hhmm(day.get("end") or prefs["day_end"])
        if day_start is None:
            problems.append(f"{where}: start must be HH:MM")
            continue
        if day_end is None:
            problems.append(f"{where}: end must be HH:MM")
            continue
        if _minutes(day_end) <= _minutes(day_start):
            problems.append(f"{where}: end must be after start")
            continue
        if "early_mornings" in prefs["avoid"] and _minutes(day_start) < 8 * 60:
            problems.append(f"{where}: starts at {day.get('start') or prefs['day_start']}, but early mornings are avoided")
        stops = day.get("stops") or []
        if not isinstance(stops, list):
            problems.append(f"{where}: stops must be a list")
            continue
        if len(stops) > MAX_STOPS[prefs["pace"]]:
            problems.append(
                f"{where}: {len(stops)} stops is more than the {prefs['pace']} pace allows ({MAX_STOPS[prefs['pace']]})"
            )
        clock = _minutes(day_start)
        travel_total = 0
        names = set()
        for j, stop in enumerate(stops):
            at = f"{where}, stop {j + 1}"
            if not isinstance(stop, dict) or not str(stop.get("name") or "").strip():
                problems.append(f"{at}: needs a name")
                continue
            name = str(stop["name"]).strip()
            at = f"{where}, {name!r}"
            if name.lower() in names:
                problems.append(f"{at}: appears twice on the day")
            names.add(name.lower())
            duration = stop.get("duration_minutes", 60)
            if not isinstance(duration, int) or isinstance(duration, bool) or not 1 <= duration <= 1440:
                problems.append(f"{at}: duration_minutes must be 1-1440")
                continue
            travel = stop.get("travel_minutes_from_prev", 0)
            if not isinstance(travel, int) or isinstance(travel, bool) or travel < 0:
                problems.append(f"{at}: travel_minutes_from_prev must be 0 or more")
                travel = 0
            clock += travel
            travel_total += travel
            arrival = clock
            departure = clock + duration
            if departure > _minutes(day_end):
                problems.append(f"{at}: ends at {_mm(departure)}, after the day ends at {day.get('end') or prefs['day_end']}")
            opens, closes = _hhmm(stop.get("opens")), _hhmm(stop.get("closes"))
            if opens and closes:
                if _minutes(closes) >= _minutes(opens):
                    if arrival < _minutes(opens) or departure > _minutes(closes):
                        problems.append(f"{at}: open {stop['opens']}-{stop['closes']}, visit is {_mm(arrival)}-{_mm(departure)}")
                elif arrival < _minutes(opens):
                    problems.append(f"{at}: opens at {stop['opens']}, visit starts at {_mm(arrival)}")
            clock = departure
        if travel_total > prefs["max_daily_travel_minutes"]:
            problems.append(
                f"{where}: {travel_total} minutes of travel, over the {prefs['max_daily_travel_minutes']}-minute limit"
            )

    budget = plan.get("budget")
    summary = None
    if isinstance(budget, dict):
        total = 0.0
        items = budget.get("items") or []
        if not isinstance(items, list):
            problems.append("budget.items must be a list")
            items = []
        for i, item in enumerate(items):
            where = f"budget.items[{i}]"
            if not isinstance(item, dict):
                problems.append(f"{where}: must be an object")
                continue
            amount = item.get("amount", item.get("total_price"))
            if not isinstance(amount, (int, float)) or isinstance(amount, bool) or amount < 0:
                problems.append(f"{where}: amount must be 0 or more")
                continue
            if item.get("currency") and str(item["currency"]).upper() != currency:
                problems.append(f"{where}: {item['currency']} is not the trip currency {currency}")
                continue
            total += float(amount)
        if budget.get("currency") and str(budget["currency"]).upper() != currency:
            problems.append(f"budget.currency {budget['currency']} is not the trip currency {currency}")
        target = budget.get("target")
        if isinstance(target, (int, float)) and not isinstance(target, bool) and total > float(target):
            problems.append(f"budget totals {total:g} {currency}, over the target {float(target):g}")
        summary = {
            "total": round(total, 2),
            "per_person": round(total / travelers, 2) if travelers else None,
            "currency": currency,
        }
    return {"ok": not problems, "problems": problems, "summary": summary}


def _date(text, where: str, problems: list[str]) -> date | None:
    try:
        return date.fromisoformat(str(text))
    except (ValueError, TypeError):
        problems.append(f"{where} must be YYYY-MM-DD, got {text!r}")
        return None


def _traveler_count(value, problems: list[str]) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        if value < 1:
            problems.append("travelers must be at least 1")
            return 0
        return value
    if isinstance(value, dict):
        total = sum(v for v in value.values() if isinstance(v, int) and not isinstance(v, bool) and v >= 0)
        if total < 1:
            problems.append("travelers must add up to at least 1")
        return total
    problems.append("travelers must be a number or {adults, children, infants}")
    return 0


def _mm(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


RULES = {
    "visa": (30, "10:00", 0, "Apply for the visa for {title}", "The passport and the destination's rules decide this; do it early."),
    "vaccinations": (30, "10:00", 0, "Check vaccinations for {title}", "Check the destination's requirements and allow time for a course."),
    "insurance": (14, "10:00", 0, "Arrange travel insurance for {title}", "Check it covers the activities and the dates."),
    "check_in": (1, None, 0, "Check in for {title}", "Online check-in usually opens 24 hours before departure."),
    "pack": (1, "18:00", 60, "Pack for {title}", "Use the TREK packing list; leave out what the weather does not need."),
    "house": (1, "17:00", 0, "Get the house ready before {title}", "Bins, plants, pets, keys, and anything left running."),
    "currency": (7, "10:00", 0, "Get {currency} and check cards for {title}", "Tell the bank about the dates; carry a small amount of cash."),
    "roaming": (3, "10:00", 0, "Set up roaming or an eSIM for {title}", "Check the plan and the phone before you go."),
    "car": (3, "10:00", 0, "Check the rental car and licence for {title}", "Licence, insurance, fuel policy and the pickup time."),
    "gear": (7, "10:00", 0, "Check gear for {title}", "Everything the activities need, and nothing that will not be used."),
    "restaurant": (21, "10:00", 0, "Book the restaurants for {title}", "The places that need a reservation, at the times the days allow."),
    "documents": (2, "18:00", 0, "Copy the passports and bookings for {title}", "One copy offline, one with someone at home."),
}


def reminders(brief: dict | str, prefs: dict | str | None = None, now: datetime | None = None) -> dict:
    """Dated Life tasks for the pre-trip actions the brief asks for; the script does the date arithmetic, the model chooses
    which actions apply."""
    brief, prefs = load(brief), load(prefs or {})
    now = now or datetime.now(timezone.utc)
    prefs, problems = normalize_prefs(prefs)
    warnings: list[str] = []
    if not isinstance(brief, dict):
        return {"ok": False, "problems": problems + ["brief must be a JSON object"], "warnings": [], "tasks": []}
    title = str(brief.get("trip_title") or "").strip()
    if not title:
        problems.append("brief.trip_title is required")
    departure = _local(brief.get("departure"), "brief.departure", problems)
    if departure is None:
        return {"ok": False, "problems": problems, "warnings": warnings, "tasks": []}
    home = str(brief.get("home_time_zone") or prefs["time_zone"])
    try:
        zone = ZoneInfo(home)
    except Exception:
        return {"ok": False, "problems": problems + [f"home_time_zone {home!r} is not an IANA zone"], "warnings": [], "tasks": []}
    departure = departure.replace(tzinfo=zone)
    return_text = str(brief.get("return") or "")
    try:
        ends_on = date.fromisoformat(return_text[:10])
    except ValueError:
        ends_on = departure.date()
        warnings.append("brief.return is missing or not a date; the goal ends on the departure date")
    if ends_on < departure.date():
        problems.append(f"return {ends_on} is before departure {departure.date()}")

    goal = {"title": title, "ends_on": ends_on.isoformat()}
    if brief.get("trip_id") is not None:
        goal["notes"] = f"TREK trip id: {brief['trip_id']}"
    goal_id = brief.get("goal_id")
    currency = str(brief.get("currency") or prefs["currency"])

    rules = brief.get("rules") or []
    if not isinstance(rules, list):
        problems.append("brief.rules must be a list")
        rules = []
    rules = list(dict.fromkeys(rules))
    if "passport" in rules and brief.get("international", True):
        expiry_text = brief.get("passport_expiry")
        if not expiry_text:
            warnings.append("passport expiry not given; check that it is valid for six months after the return")
        else:
            try:
                expiry = date.fromisoformat(str(expiry_text)[:10])
            except ValueError:
                problems.append(f"passport_expiry {expiry_text!r} is not YYYY-MM-DD")
            else:
                if expiry < ends_on + timedelta(days=183):
                    problems.append(f"passport expires {expiry}, before six months after the return ({ends_on})")

    tasks: list[dict] = []
    for rule in rules:
        if rule == "passport":
            continue
        if rule not in RULES:
            problems.append(f"brief.rules has unknown {rule!r}; use {', '.join(['passport', *RULES])} or custom")
            continue
        days, clock, alert, text, notes = RULES[rule]
        if rule == "check_in":
            at = departure - timedelta(days=1)
        else:
            hour, minute = (int(x) for x in clock.split(":"))
            at = datetime.combine(departure.date() - timedelta(days=days), time(hour, minute), zone)
        _add_task(tasks, warnings, now, at, alert, text.format(title=title, currency=currency), notes, home)
    for i, custom in enumerate(brief.get("custom") or []):
        if not isinstance(custom, dict) or not str(custom.get("title") or "").strip():
            problems.append(f"brief.custom[{i}] needs a title")
            continue
        days = custom.get("days_before", 1)
        clock = custom.get("time", "10:00")
        alert = custom.get("alert_before_minutes", 0)
        if not isinstance(days, int) or isinstance(days, bool) or days < 0:
            problems.append(f"brief.custom[{i}].days_before must be 0 or more")
            continue
        parsed = _hhmm(clock)
        if parsed is None:
            problems.append(f"brief.custom[{i}].time must be HH:MM")
            continue
        if not isinstance(alert, int) or isinstance(alert, bool) or not 0 <= alert <= 10080:
            problems.append(f"brief.custom[{i}].alert_before_minutes must be 0-10080")
            continue
        at = datetime.combine(departure.date() - timedelta(days=days), parsed, zone)
        _add_task(tasks, warnings, now, at, alert, str(custom["title"]).strip(),
                  str(custom.get("notes") or ""), home)
    if not tasks and not problems:
        warnings.append("no reminders were chosen; add the rules that apply to this trip")
    out = {"ok": not problems, "problems": problems, "warnings": warnings, "goal": goal, "tasks": tasks}
    if not problems:
        out["operations"] = _operations(goal, tasks, goal_id)
        if len(out["operations"]) > MAX_BATCH:
            out["ok"] = False
            out["problems"] = [f"too many reminders ({len(tasks)}): at most {(MAX_BATCH - 1) // 2} with their links in one batch; drop the least useful"]
            del out["operations"]
    return out


def _local(text, where: str, problems: list[str]) -> datetime | None:
    for layout in ("%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(str(text), layout)
        except (ValueError, TypeError):
            pass
    problems.append(f"{where} must be YYYY-MM-DDTHH:MM with no zone, got {text!r}")
    return None


MAX_BATCH = 50   # the engine's limit on one batch_apply


def _operations(goal: dict, tasks: list[dict], goal_id) -> list[dict]:
    """The batch that creates the trip's goal (unless `brief.goal_id` names one that exists) and its reminders, each joined to the goal with a
    `serves` link, ready for life/batch_apply. The engine stores a goal as an intention."""
    intention = goal_id or str(uuid.uuid4())
    ops = []
    if not goal_id:
        ops.append({"operation": "intentions_create", "input": {k: v for k, v in {
            "id": intention, "title": goal["title"], "notes": goal.get("notes"), "ends_on": goal.get("ends_on")}.items() if v}})
    for task in tasks:
        task_id = str(uuid.uuid4())
        ops.append({"operation": "tasks_create", "input": {"id": task_id, **{k: v for k, v in task.items() if v not in (None, "")}}})
        ops.append({"operation": "links_set", "input": {
            "from_kind": "task", "from_id": task_id, "relation": "serves", "to_kind": "intention", "to_id": intention}})
    return ops


def _add_task(tasks, warnings, now, at, alert, title, notes, zone_name):
    at_utc = at.astimezone(timezone.utc)
    if now is not None and at_utc < now:
        warnings.append(f"{title!r} was due {at_utc:%Y-%m-%dT%H:%MZ}, already past; not added")
        return
    task = {
        "title": title,
        "notes": notes,
        "at": at_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "time_zone": zone_name,
        "alert_before_minutes": alert,
    }
    tasks.append(task)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Rank trip candidates, check an itinerary, or date reminders.")
    subs = parser.add_subparsers(dest="cmd", required=True)
    for name in ("rank", "check", "reminders"):
        cmd = subs.add_parser(name)
        cmd.add_argument("input", help="candidates.json, plan.json or brief.json")
        cmd.add_argument("prefs", nargs="?", default=None, help="preferences.json (optional)")
        if name == "rank":
            cmd.add_argument("--top", type=int, default=15)
    args = parser.parse_args(argv)
    if args.cmd == "rank":
        out = rank(args.input, args.prefs, top=args.top)
    elif args.cmd == "check":
        out = check(args.input, args.prefs)
    else:
        out = reminders(args.input, args.prefs)
    print(json.dumps(out, indent=1, ensure_ascii=False))
    return 0 if out.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
