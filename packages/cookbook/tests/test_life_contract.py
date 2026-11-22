"""The skills against the Life engine's contract (tests/contracts/life-operations.json, refreshed by tools/sync_life_contract.py).

Three ways a skill can drift from the engine, each of which has happened or can: it names a tool the engine no longer has (goals_* became
intentions_*), its prose still tells the model to use one, or the batch it builds contains an operation or field the engine refuses.
Refresh the snapshot when the engine changes; a failure here says what to fix in the skills.
"""
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import jsonschema
import pytest

import goalplan
import travelplan

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
CONTRACT = json.loads((ROOT / "tests" / "contracts" / "life-operations.json").read_text())
OPERATIONS = CONTRACT["operations"]
# Names the engine used to have. A skill that still says one of these is out of date, even if the word looks harmless.
RETIRED_PREFIXES = {"goals", "views", "library", "measurements", "tracker_catalog"}
# `tasks`, `calendar_events`, ... : everything before the last underscore of an operation name
PREFIXES = {name.rsplit("_", 1)[0] for name in OPERATIONS} | RETIRED_PREFIXES
# A tool name is one of those prefixes plus a verb the engine's operations end in (or one it used to), so a field like `day_start` is not one.
SUFFIXES = {name.rsplit("_", 1)[1] for name in OPERATIONS} | {"create", "list", "get", "update", "archive", "restore", "delete"}
TOKEN = re.compile(r"\b(?:" + "|".join(sorted(PREFIXES, key=len, reverse=True)) + r")_(?:" + "|".join(sorted(SUFFIXES, key=len, reverse=True)) + r")\b")


def skill_texts():
    for path in sorted(SKILLS.rglob("*.md")):
        if "references" in path.parts or "assets" in path.parts:   # background reading, not instructions that name tools
            continue
        yield path, path.read_text()


def life_tool_names(text):
    return {m.group(0) for m in TOKEN.finditer(text)}


def test_the_snapshot_is_the_engines_and_not_empty():
    assert len(OPERATIONS) > 50 and "intentions_create" in OPERATIONS and "goals_create" not in OPERATIONS, CONTRACT["source"]


def test_no_skill_text_names_a_life_tool_the_engine_does_not_have():
    stale = {}
    for path, text in skill_texts():
        bad = {n for n in life_tool_names(text) if n not in OPERATIONS}
        if bad:
            stale[str(path.relative_to(SKILLS))] = sorted(bad)
    assert not stale, stale


def validate_batch(operations, label):
    batchable = set(re.findall(r"[a-z_]+_(?:create|record|set)", OPERATIONS["batch_apply"]["properties"]["operations"]["items"]["properties"]["operation"]["description"]))
    assert 1 <= len(operations) <= 50, f"{label}: {len(operations)} operations (a batch holds 1-50)"
    for i, op in enumerate(operations):
        assert op["operation"] in batchable, f"{label}[{i}]: {op['operation']} cannot be part of a batch"
        jsonschema.validate({**op["input"], "idempotency_key": "k"}, OPERATIONS[op["operation"]])


def test_the_goal_plan_batch_is_one_the_engine_accepts():
    plan = {"goal": {"title": "Run a 10K by March", "notes": "slowly", "ends_on": "2027-03-15"},
            "tasks": [{"title": "Buy shoes", "at": "2026-11-20T10:00", "minutes": 30, "alert_before_minutes": 15},
                      {"title": "Long run", "at": "2026-11-22T08:00", "recurrence": {"freq": "weekly", "weekdays": [0]}, "is_priority": True},
                      {"title": "Stretch"}],
            "events": [{"title": "Race day", "at": "2027-03-14T08:00", "minutes": 120, "alert_before_minutes": 60}]}
    assert not goalplan.check(plan, "America/Los_Angeles", datetime(2026, 11, 14, tzinfo=timezone.utc))
    ops, _ = goalplan.build_operations(plan, "America/Los_Angeles", lambda: str(uuid.uuid4()))
    validate_batch(ops, "goal plan")


@pytest.mark.parametrize("existing_goal", [False, True])
def test_the_trip_reminder_batch_is_one_the_engine_accepts(existing_goal):
    brief = {"trip_title": "Lisbon", "departure": "2026-12-10T08:00", "return": "2026-12-15T20:00", "home_time_zone": "Europe/Lisbon",
             "rules": ["passport", "check_in", "pack", "house"], "trip_id": 7, "passport_expiry": "2030-01-01", "international": True}
    if existing_goal:
        brief["goal_id"] = str(uuid.uuid4())
    out = travelplan.reminders(brief, {"time_zone": "Europe/Lisbon"}, now=datetime(2026, 11, 1, tzinfo=timezone.utc))
    assert out["ok"], out["problems"]
    validate_batch(out["operations"], "trip reminders")
