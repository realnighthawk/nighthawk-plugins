"""The mechanical part of setting up a goal: check a plan, turn it into the engine's batch, describe what was made.

Pure functions, no network: the script reads the clock, the zone and the ids; the model calls the engine. Rules mirror the
life engine's own (item/goal validation, recurring-alert limits) so every problem in a plan is found in one pass, before
the engine would stop at the first.

  python3 scripts/goalplan.py check plan.json --tz <zone>
  python3 scripts/goalplan.py build plan.json --tz <zone>
"""

from __future__ import annotations

import argparse
import json
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

# A batch holds at most 50 operations and every task or event needs its own link to the goal, so a plan holds at most 24 of them:
# 1 (the goal) + 2 * 24 = 49.
MAX_ITEMS = 24
_LAYOUTS = ("%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S")


def parse_local(text: str, tz: ZoneInfo) -> datetime:
    """A local wall-clock time with an hour and no zone, in the person's zone."""
    for layout in _LAYOUTS:
        try:
            return datetime.strptime(text, layout).replace(tzinfo=tz)
        except (ValueError, TypeError):
            pass
    raise ValueError(f"{text!r} is not a local time: write YYYY-MM-DDTHH:MM with an hour and no zone")


def check(plan: dict, tz_name: str, now: datetime) -> list[str]:
    """Every problem in the plan, each naming the item. Empty means it is fit to try."""
    problems: list[str] = []
    add = problems.append
    tz = ZoneInfo(tz_name)
    now = now.astimezone(tz)

    goal = plan.get("goal") or {}
    tasks, events = plan.get("tasks") or [], plan.get("events") or []

    def title(where: str, item: dict) -> None:
        if not 1 <= len(str(item.get("title") or "").strip()) <= 200:
            add(f"{where}: title must be 1-200 characters")
        if len(str(item.get("notes") or "")) > 2000:
            add(f"{where}: notes must be at most 2000 characters")

    title("goal", goal)
    ends = None
    if goal.get("ends_on"):
        try:
            last = date.fromisoformat(goal["ends_on"])
        except ValueError:
            add(f"goal: ends_on {goal['ends_on']!r} must be YYYY-MM-DD")
        else:
            if last < now.date():
                add(f"goal: ends_on {goal['ends_on']} is in the past (today is {now.date()})")
            ends = datetime.combine(last + timedelta(days=1), datetime.min.time(), tz)  # runs through its last day
    if not tasks and not events:
        add("the plan has no tasks or events: give the goal at least one next action")
    if len(tasks) + len(events) > MAX_ITEMS:
        add(f"too many items ({len(tasks)} tasks and {len(events)} events): at most {MAX_ITEMS} together, group small ones")

    def when(where: str, text: str, repeating: bool) -> datetime | None:
        try:
            t = parse_local(text, tz)
        except ValueError as e:
            add(f"{where}: {e}")
            return None
        if not repeating and t < now:
            add(f"{where}: {text} is in the past (now is {now:%Y-%m-%dT%H:%M})")
        if not repeating and ends is not None and t >= ends:
            add(f"{where}: {text} is after the goal ends ({goal['ends_on']})")
        return t

    def minutes(where: str, value) -> None:
        if value is not None and not (isinstance(value, int) and 1 <= value <= 1440):
            add(f"{where}: minutes must be 1-1440")

    def alert(where: str, item: dict, at: datetime | None, rec: dict | None) -> None:
        before = item.get("alert_before_minutes")
        if before is None:
            return
        if not item.get("at"):
            add(f"{where}: alert_before_minutes needs at")
        elif not (isinstance(before, int) and 0 <= before <= 10080):
            add(f"{where}: alert_before_minutes must be 0-10080")
        elif rec is not None and at is not None and (msg := _recurring_alert_problem(at, before, rec)):
            add(f"{where}: {msg}")

    for i, t in enumerate(tasks):
        where = f"tasks[{i}] {t.get('title', '')!r}"
        title(where, t)
        minutes(where, t.get("minutes"))
        rec = t.get("recurrence")
        if rec is not None and not t.get("at"):
            add(f"{where}: a repeat needs at")
        at = when(where, t["at"], rec is not None) if t.get("at") else None
        if rec is not None:
            _recurrence(add, where, rec)
        alert(where, t, at, rec)
    for i, e in enumerate(events):
        where = f"events[{i}] {e.get('title', '')!r}"
        title(where, e)
        minutes(where, e.get("minutes"))
        at = None
        if not e.get("at"):
            add(f"{where}: an event happens at a time: give at")
        else:
            at = when(where, e["at"], False)
        alert(where, e, at, None)
    return problems


def _recurrence(add, where: str, rec: dict) -> None:
    freq = rec.get("freq")
    if freq not in ("daily", "weekly", "monthly"):
        add(f"{where}: recurrence.freq must be daily, weekly or monthly")
        return
    interval = rec.get("interval", 1)
    if not (isinstance(interval, int) and 1 <= interval <= 365):
        add(f"{where}: recurrence.interval must be 1-365")
    weekdays = rec.get("weekdays") or []
    if weekdays and freq != "weekly":
        add(f"{where}: recurrence.weekdays is for weekly repeats only")
    if any(not (isinstance(d, int) and 0 <= d <= 6) for d in weekdays):
        add(f"{where}: recurrence.weekdays are 0 (Sunday) to 6")


def _recurring_alert_problem(at: datetime, before: int, rec: dict) -> str:
    """The engine's limits on a repeating item's alert: it must fall on the item's own day, and only some repeat shapes
    can carry one."""
    if (at - timedelta(minutes=before)).date() != at.date():
        return "a repeating item's alert must fall on the same day as the item: use fewer minutes before, or no alert"
    interval = rec.get("interval") or 1
    if rec.get("freq") == "weekly" and interval > 1 and rec.get("weekdays"):
        return "an alert cannot repeat every other week (or less often) on chosen weekdays; repeat every week, or on one weekday"
    if rec.get("freq") == "monthly" and interval != 1:
        return "an alert cannot repeat every few months; repeat monthly, or leave the alert off"
    return ""


def _utc(text: str, tz: ZoneInfo) -> str:
    return parse_local(text, tz).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_operations(plan: dict, tz_name: str, new_id) -> tuple[list[dict], str]:
    """The batch for a checked plan, in the order the engine needs (the goal, then what serves it, then the links), and the goal's id.
    The engine stores a goal as an intention and joins each task or event to it with a `serves` link, so ids, links, UTC instants and
    the time zone are filled in here, not by the model."""
    tz = ZoneInfo(tz_name)
    goal = plan["goal"]
    goal_id = new_id()
    ops = [{"operation": "intentions_create", "input": _drop_empty({
        "id": goal_id, "title": goal["title"].strip(), "notes": goal.get("notes"), "ends_on": goal.get("ends_on")})}]
    serving: list[tuple[str, str]] = []   # (kind, id) of everything that serves the goal
    for t in plan.get("tasks") or []:
        item = {"id": new_id(), "title": t["title"].strip(), "notes": t.get("notes"), "minutes": t.get("minutes"),
                "alert_before_minutes": t.get("alert_before_minutes"), "is_priority": t.get("is_priority") or None}
        if t.get("at"):
            item.update(at=_utc(t["at"], tz), time_zone=tz_name)
        if t.get("recurrence"):
            item["recurrence"] = t["recurrence"]
        ops.append({"operation": "tasks_create", "input": _drop_empty(item)})
        serving.append(("task", item["id"]))
    for e in plan.get("events") or []:
        item = {"id": new_id(), "title": e["title"].strip(), "notes": e.get("notes"), "at": _utc(e["at"], tz),
                "time_zone": tz_name, "minutes": e.get("minutes"), "alert_before_minutes": e.get("alert_before_minutes")}
        ops.append({"operation": "calendar_events_create", "input": _drop_empty(item)})
        serving.append(("event", item["id"]))
    for kind, item_id in serving:
        ops.append({"operation": "links_set", "input": {
            "from_kind": kind, "from_id": item_id, "relation": "serves", "to_kind": "intention", "to_id": goal_id}})
    return ops, goal_id


def _drop_empty(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None and v != ""}


def facts(plan: dict, goal_id: str, undo_key: str, tz_name: str) -> dict:
    """What was made, in the words a reply needs: local times, which items will tell the person ahead."""
    def line(item: dict) -> dict:
        out = {"title": item["title"].strip(), "when": item.get("at") or None}
        if item.get("recurrence"):
            out["repeats"] = item["recurrence"]["freq"]
        if item.get("alert_before_minutes") is not None:
            out["alert_minutes_before"] = item["alert_before_minutes"]
        return out

    goal = plan["goal"]
    return {
        "ok": True, "undo_key": undo_key, "time_zone": tz_name,
        "goal": {"id": goal_id, "title": goal["title"].strip(), "ends_on": goal.get("ends_on")},
        "tasks": [line(t) for t in plan.get("tasks") or []],
        "events": [line(e) for e in plan.get("events") or []],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Check a goal plan or build the Life engine batch.")
    subs = parser.add_subparsers(dest="cmd", required=True)
    for name in ("check", "build"):
        cmd = subs.add_parser(name)
        cmd.add_argument("plan", help="plan.json")
        cmd.add_argument("--tz", required=True, help="the person's IANA time zone")
    args = parser.parse_args(argv)
    try:
        plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(json.dumps({"ok": False, "problems": [f"could not read {args.plan}: {e}"]}, indent=1))
        return 1
    problems = check(plan, args.tz, datetime.now(timezone.utc))
    if problems or args.cmd == "check":
        print(json.dumps({"ok": not problems, "problems": problems}, indent=1))
        return 0 if not problems else 1
    key = str(uuid.uuid4())
    operations, goal_id = build_operations(plan, args.tz, lambda: str(uuid.uuid4()))
    print(json.dumps({
        "ok": True,
        "goal_id": goal_id,
        "idempotency_key": key,
        "operations": operations,
        "summary": facts(plan, goal_id, key, args.tz),
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
