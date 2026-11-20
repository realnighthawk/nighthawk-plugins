import json
from datetime import datetime, timezone

import pytest

import travelplan


def test_preferences_are_normalized_and_bad_values_are_named():
    prefs, problems = travelplan.normalize_prefs({"pace": "warp", "travelers": {"adults": 2, "children": 1}})
    assert any("pace" in p for p in problems)
    assert prefs["pace"] == "balanced"
    assert prefs["travelers"] == {"adults": 2, "children": 1, "infants": 0}


def test_rank_puts_must_see_first_and_excludes_the_never_list():
    candidates = [
        {"name": "City Museum", "types": ["museum"], "rating": 4.7, "ratings_count": 800,
         "price_level": 2, "distance_km": 2},
        {"name": "Nightclub X", "types": ["night_club"], "rating": 4.9, "ratings_count": 9000,
         "price_level": 3, "distance_km": 1},
        {"name": "Must See Tower", "types": ["monument"], "rating": 4.5, "ratings_count": 3000,
         "price_level": 1, "distance_km": 4},
    ]
    prefs = {"interests": ["culture"], "priorities": ["culture"], "must_see": ["Tower"],
             "never": ["nightclubs"], "budget": "mid"}
    out = travelplan.rank(candidates, prefs)
    assert out["ok"]
    names = [r["name"] for r in out["ranking"]]
    assert names[0] == "Must See Tower"
    assert "Nightclub X" not in names
    assert "must-see" in out["ranking"][0]["reasons"]


def test_rank_penalizes_over_budget_and_distance():
    candidates = [
        {"name": "Cheap Nearby", "types": ["restaurant"], "rating": 4.0, "price_level": 1, "distance_km": 1},
        {"name": "Luxury Far", "types": ["restaurant"], "rating": 4.8, "price_level": 4, "distance_km": 10},
    ]
    prefs = {"budget": "shoestring", "pace": "relaxed", "priorities": ["minimize_transit"]}
    out = travelplan.rank(candidates, prefs)
    assert [r["name"] for r in out["ranking"]] == ["Cheap Nearby", "Luxury Far"]
    assert "over budget" in out["ranking"][1]["reasons"]


def test_check_catches_overrun_closed_stop_and_budget_problems():
    plan = {
        "start": "2026-06-03", "end": "2026-06-03", "currency": "EUR", "travelers": 2,
        "days": [{
            "date": "2026-06-03", "start": "09:00", "end": "18:00",
            "stops": [
                {"name": "Museum", "duration_minutes": 300},
                {"name": "Dinner", "duration_minutes": 300, "opens": "10:00", "closes": "12:00"},
            ],
        }],
        "budget": {"target": 100, "items": [
            {"category": "food", "amount": 200, "currency": "EUR"},
            {"category": "taxi", "amount": 50, "currency": "USD"},
        ]},
    }
    out = travelplan.check(plan, {"pace": "relaxed"})
    assert not out["ok"]
    assert any("after the day ends" in p for p in out["problems"])
    assert any("open 10:00-12:00" in p for p in out["problems"])
    assert any("not the trip currency" in p for p in out["problems"])
    assert any("over the target" in p for p in out["problems"])
    assert out["summary"] == {"total": 200.0, "per_person": 100.0, "currency": "EUR"}


def test_check_catches_wrong_day_travel_limit_and_pace():
    plan = {
        "start": "2026-06-03", "end": "2026-06-04", "currency": "EUR",
        "days": [
            {"date": "2026-06-05", "start": "09:00", "end": "18:00", "stops": []},
            {"date": "2026-06-03", "start": "09:00", "end": "18:00", "stops": [
                {"name": f"Stop {i}", "duration_minutes": 30, "travel_minutes_from_prev": 40} for i in range(5)
            ]},
            {"date": "2026-06-03", "start": "09:00", "end": "18:00", "stops": []},
        ],
    }
    out = travelplan.check(plan, {"pace": "relaxed", "max_daily_travel_minutes": 90})
    assert any("outside the trip" in p for p in out["problems"])
    assert any("appears twice" in p for p in out["problems"])
    assert any("more than the relaxed pace" in p for p in out["problems"])
    assert any("minutes of travel" in p for p in out["problems"])


def test_reminders_compute_local_times_and_passport_validity():
    brief = {
        "trip_title": "Lisbon", "trip_id": 42, "departure": "2026-06-03T10:00",
        "return": "2026-06-10", "home_time_zone": "Europe/Lisbon",
        "rules": ["passport", "check_in", "pack"], "passport_expiry": "2030-01-01",
        "international": True, "currency": "EUR",
    }
    out = travelplan.reminders(brief, {"time_zone": "UTC"},
                               now=datetime(2026, 5, 1, tzinfo=timezone.utc))
    assert out["ok"] and not out["problems"]
    assert out["goal"]["ends_on"] == "2026-06-10"
    check_in = next(t for t in out["tasks"] if t["title"].startswith("Check in"))
    pack = next(t for t in out["tasks"] if t["title"].startswith("Pack"))
    assert check_in["at"] == "2026-06-02T09:00:00Z"  # 10:00 WEST, 24h before
    assert pack["at"] == "2026-06-02T17:00:00Z"        # 18:00 WEST the day before
    assert pack["alert_before_minutes"] == 60

    brief["passport_expiry"] = "2026-11-01"
    out = travelplan.reminders(brief, {"time_zone": "Europe/Lisbon"},
                               now=datetime(2026, 5, 1, tzinfo=timezone.utc))
    assert any("six months after the return" in p for p in out["problems"])


def test_reminders_skip_past_tasks_and_accept_custom_ones():
    brief = {
        "trip_title": "Porto", "departure": "2026-06-03T10:00", "return": "2026-06-08",
        "home_time_zone": "Europe/Lisbon", "rules": ["pack"],
        "custom": [{"title": "Book the Douro tour", "days_before": 0, "time": "12:00"}],
    }
    out = travelplan.reminders(brief, {"time_zone": "Europe/Lisbon"},
                               now=datetime(2026, 6, 3, 10, 0, tzinfo=timezone.utc))
    titles = [t["title"] for t in out["tasks"]]
    assert "Book the Douro tour" in titles
    assert not any(t.startswith("Pack") for t in titles)
    assert any("already past" in w for w in out["warnings"])


def test_a_function_takes_the_data_or_the_path_of_a_json_file(tmp_path):
    import travelplan
    candidates = [{"name": "Colosseum", "types": ["tourist_attraction"], "rating": 4.7, "ratings_count": 1000, "distance_km": 2}]
    (tmp_path / "c.json").write_text(json.dumps(candidates))
    assert travelplan.rank(str(tmp_path / "c.json"), None, top=3) == travelplan.rank(candidates, {}, top=3)
    with pytest.raises(OSError):
        travelplan.rank(str(tmp_path / "missing.json"))


def test_the_reminders_come_as_a_batch_that_creates_the_goal_and_links_each_task_to_it():
    brief = {"trip_title": "Lisbon", "departure": "2026-12-10T08:00", "return": "2026-12-15T20:00", "home_time_zone": "Europe/Lisbon",
             "rules": ["check_in", "pack"], "trip_id": 7}
    out = travelplan.reminders(brief, {"time_zone": "Europe/Lisbon"}, now=datetime(2026, 11, 1, tzinfo=timezone.utc))
    assert out["ok"], out
    ops = out["operations"]
    assert ops[0]["operation"] == "intentions_create" and ops[0]["input"]["ends_on"] == "2026-12-15"
    goal_id = ops[0]["input"]["id"]
    creates = [o["input"] for o in ops if o["operation"] == "tasks_create"]
    links = [o["input"] for o in ops if o["operation"] == "links_set"]
    assert len(creates) == len(links) == len(out["tasks"]) > 0
    assert all("goal_id" not in c for c in creates)
    assert {(l["from_id"], l["to_id"]) for l in links} == {(c["id"], goal_id) for c in creates}
    assert all(l["relation"] == "serves" and l["to_kind"] == "intention" for l in links)


def test_an_existing_goal_gets_only_the_tasks_and_their_links():
    brief = {"trip_title": "Lisbon", "departure": "2026-12-10T08:00", "return": "2026-12-15T20:00", "home_time_zone": "Europe/Lisbon",
             "rules": ["check_in"], "goal_id": "existing-goal"}
    out = travelplan.reminders(brief, {"time_zone": "Europe/Lisbon"}, now=datetime(2026, 11, 1, tzinfo=timezone.utc))
    assert out["ok"], out
    assert [o["operation"] for o in out["operations"]] == ["tasks_create", "links_set"] * len(out["tasks"])
    assert all(o["input"]["to_id"] == "existing-goal" for o in out["operations"] if o["operation"] == "links_set")
