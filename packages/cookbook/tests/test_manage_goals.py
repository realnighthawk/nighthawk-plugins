import json
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import goalplan

NOW = datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)
TZ = "America/Los_Angeles"  # UTC-7 in October


def plan(**over):
    p = {"goal": {"title": "Run a 10K", "ends_on": "2026-12-20"},
         "tasks": [{"title": "Buy shoes", "at": "2026-10-30T18:00"}], "events": []}
    p.update(over)
    return p


def ids():
    n = iter(range(1, 100))
    return lambda: f"id-{next(n)}"


def test_a_good_plan_has_no_problems():
    assert goalplan.check(plan(), TZ, NOW) == []


def test_every_problem_is_found_in_one_pass():
    bad = plan(goal={"title": "", "ends_on": "2026-10-01"},
               tasks=[{"title": "x" * 201, "at": "2026-10-30"}, {"title": "Late", "at": "2027-01-05T09:00"},
                      {"title": "Past", "at": "2026-10-20T09:00"}],
               events=[{"title": "Flight"}, {"title": "Dinner", "at": "2026-10-31T19:00", "minutes": 0}])
    out = goalplan.check(bad, TZ, NOW)
    text = "\n".join(out)
    for want in ("goal: title", "ends_on 2026-10-01 is in the past", "tasks[0]", "not a local time", "is in the past",
                 "events[0]", "give at", "minutes must be 1-1440"):
        assert want in text, (want, out)
    assert len(out) >= 6


def test_a_time_after_the_goal_ends_is_refused():
    out = goalplan.check(plan(tasks=[{"title": "Too late", "at": "2026-12-21T09:00"}]), TZ, NOW)
    assert any("after the goal ends" in p for p in out)
    assert goalplan.check(plan(tasks=[{"title": "Last day", "at": "2026-12-20T23:00"}]), TZ, NOW) == []


def test_a_repeating_alert_must_stay_on_its_day_and_have_a_supported_shape():
    daily = {"title": "Run", "at": "2026-10-26T06:30", "recurrence": {"freq": "daily"}}
    assert goalplan.check(plan(tasks=[{**daily, "alert_before_minutes": 15}]), TZ, NOW) == []
    out = goalplan.check(plan(tasks=[{**daily, "alert_before_minutes": 600}]), TZ, NOW)
    assert any("same day" in p for p in out)
    biweekly = {"title": "Long run", "at": "2026-10-31T08:00", "alert_before_minutes": 10,
                "recurrence": {"freq": "weekly", "interval": 2, "weekdays": [6]}}
    assert any("every other week" in p for p in goalplan.check(plan(tasks=[biweekly]), TZ, NOW))
    assert any("needs at" in p for p in goalplan.check(plan(tasks=[{"title": "x", "alert_before_minutes": 5}]), TZ, NOW))


def test_a_plan_with_nothing_to_do_is_refused():
    out = goalplan.check(plan(tasks=[]), TZ, NOW)
    assert any("no tasks or events" in p for p in out)


# What the Life engine accepts in a batch (life-engine/internal/engine/batch.go, `batchable`): creates only.
BATCHABLE = {"intentions_create", "commitments_create", "states_create", "activities_record", "links_set", "tasks_create",
             "calendar_events_create"}


def test_the_batch_has_ids_links_and_utc_instants():
    p = plan(tasks=[{"title": "Drink water", "at": "2026-10-26T08:00", "alert_before_minutes": 0,
                     "recurrence": {"freq": "daily"}}],
             events=[{"title": "Race", "at": "2026-12-20T09:00", "minutes": 90}])
    ops, goal_id = goalplan.build_operations(p, TZ, ids())
    # the goal is an intention, what serves it follows, and each task or event is joined to it by a `serves` link
    assert [o["operation"] for o in ops] == ["intentions_create", "tasks_create", "calendar_events_create", "links_set", "links_set"]
    assert all(o["operation"] in BATCHABLE for o in ops)
    goal, task, event, link_task, link_event = (o["input"] for o in ops)
    assert goal["id"] == goal_id == "id-1" and goal["ends_on"] == "2026-12-20"
    assert "goal_id" not in task and "goal_id" not in event   # the engine has no such field any more
    assert task["at"] == "2026-10-26T15:00:00Z" and task["time_zone"] == TZ
    assert task["recurrence"] == {"freq": "daily"} and task["alert_before_minutes"] == 0
    assert event["at"] == "2026-12-20T17:00:00Z" and event["minutes"] == 90
    assert link_task == {"from_kind": "task", "from_id": task["id"], "relation": "serves", "to_kind": "intention", "to_id": goal_id}
    assert link_event == {"from_kind": "event", "from_id": event["id"], "relation": "serves", "to_kind": "intention", "to_id": goal_id}
    assert "notes" not in task and "is_priority" not in task  # empty fields are not sent


def test_a_plan_fits_one_batch_of_at_most_fifty_operations():
    many = [{"title": f"task {i}"} for i in range(goalplan.MAX_ITEMS)]
    ops, _ = goalplan.build_operations(plan(tasks=many), TZ, ids())
    assert len(ops) == 1 + 2 * goalplan.MAX_ITEMS <= 50
    problems = goalplan.check(plan(tasks=many + [{"title": "one too many"}]), TZ, NOW)
    assert any("too many items" in p and str(goalplan.MAX_ITEMS) in p for p in problems)
    # tasks and events count together
    half = [{"title": f"t{i}"} for i in range(goalplan.MAX_ITEMS)]
    assert any("too many items" in p for p in goalplan.check(plan(tasks=half, events=[{"title": "e", "at": "2026-12-20T09:00"}]), TZ, NOW))


def test_the_facts_carry_what_a_reply_needs():
    f = goalplan.facts(plan(events=[{"title": "Race", "at": "2026-12-20T09:00", "alert_before_minutes": 60}]), "g1", "k1", TZ)
    assert f["ok"] and f["undo_key"] == "k1" and f["goal"]["id"] == "g1"
    assert f["tasks"][0] == {"title": "Buy shoes", "when": "2026-10-30T18:00"}
    assert f["events"][0]["alert_minutes_before"] == 60 and "view" not in f


def test_the_cli_checks_then_builds_a_batch(tmp_path):
    day = (date.today() + timedelta(days=10)).isoformat()
    end = (date.today() + timedelta(days=30)).isoformat()
    plan = {"goal": {"title": "Run a 10K", "ends_on": end},
            "tasks": [{"title": "Buy shoes", "at": f"{day}T10:00"}], "events": []}
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan))
    script = Path(__file__).resolve().parents[1] / "skills" / "manage-goals" / "scripts" / "goalplan.py"

    check = subprocess.run([sys.executable, str(script), "check", str(path), "--tz", "UTC"], capture_output=True, text=True)
    assert check.returncode == 0, check.stdout
    assert json.loads(check.stdout) == {"ok": True, "problems": []}

    build = subprocess.run([sys.executable, str(script), "build", str(path), "--tz", "UTC"], capture_output=True, text=True)
    assert build.returncode == 0, build.stdout
    data = json.loads(build.stdout)
    assert data["operations"][0]["operation"] == "intentions_create"
    assert data["goal_id"] == data["operations"][0]["input"]["id"]
    assert data["idempotency_key"] and data["summary"]["undo_key"] == data["idempotency_key"]
