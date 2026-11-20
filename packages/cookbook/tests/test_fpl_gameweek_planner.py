import json
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[1] / "skills" / "fpl-gameweek-planner"


import fpl_flow
import fpl_plan


@pytest.fixture
def flow():
    return fpl_flow


def test_inputs_without_a_numeric_team_stop_the_step_with_a_reason(flow, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "inputs.json").write_text(json.dumps({"team": "not-a-number"}))
    with pytest.raises(flow.StepFailed, match="numeric FPL team id"):
        flow.load_inputs()
    with pytest.raises(flow.StepFailed, match="cannot read"):
        flow.load_inputs("missing.json")


def test_the_planner_output_is_kept_and_its_failure_is_the_steps_reason(flow, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    calls = []

    def run_all(**arguments):
        calls.append(arguments)
        print("table")

    monkeypatch.setattr(fpl_plan, "run_all", run_all)
    flow.fetch(7, 77)
    assert calls == [{"team": 7, "league": 77}] and (tmp_path / "fpl-output.txt").read_text() == "table\n"

    def broken(**arguments):
        print("partial")
        raise fpl_plan.PlannerError("could not reach the FPL API")

    monkeypatch.setattr(fpl_plan, "run_all", broken)
    with pytest.raises(flow.StepFailed, match="could not reach the FPL API"):
        flow.fetch(7, 77)


def test_rivals_are_formatted_from_a_saved_reply(flow, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "rivals.json").write_text(json.dumps({"result": RIVALS}))
    flow.rivals("rivals.json")
    text = (tmp_path / "rivals.md").read_text()
    assert "you are 5 with 468 points" in text


HUB = {  # the shape fpl_manager_hub returns, trimmed
    "team_id": 2452109, "gameweek": 8, "prepping_for": "GW9", "bank": 0.2, "squad_value": 101.0, "total_budget": 101.2,
    "manager_status": {"free_transfers": 1, "overall_rank": 3187654, "total_points": 468,
                       "chips_used": [{"name": "wildcard", "gameweek": 8}], "chips_remaining": ["3xc", "bboost", "freehit"],
                       "chip_active_this_gw": "wildcard"},
    "squad": [{"name": "Raya"}, {"name": "Tavernier"}, {"name": "Haaland"}],
    "squad_health": {"injured_or_doubtful": [{"name": "Calafiori", "status": "d"}],
                     "poor_form_starters": [{"name": "Bogle", "form": 1.0}]},
    "price_predictions": {"likely_risers": [{"player": {"name": "Tavernier"}}, {"player": {"name": "N.Jackson"}}],
                          "likely_fallers": [{"player": {"name": "Gonzalo"}}]},
}


def test_the_profile_keeps_the_numbers_the_person_would_otherwise_be_asked_for(flow):
    text = flow.summarize_profile(HUB)
    assert "Bank 0.2m, free transfers 1" in text
    assert "already played: wildcard (GW8)" in text and "Available for GW9: 3xc, bboost, freehit" in text
    assert "Active this gameweek" not in text   # the tool's flag is for the gameweek just played; it read as available now
    assert "Calafiori (d)" in text and "Bogle (1.0)" in text
    assert "rising Tavernier;" in text and "N.Jackson" not in text   # only moves that touch the squad
    assert "total_budget 101.2m is at CURRENT prices" in text and "printed below" in text and len(text) < 1200


RIVALS = {
    "league_name": "Squad IITI", "total_managers": 9, "standings_as_of_gw": 8,
    "your_position": {"rank": 5, "total_points": 468},
    "rivals": [{"rank": 4, "team_name": "Cero Miedo XI", "manager_name": "Palash", "total_points": 474, "point_gap": -6,
                "gap_direction": "behind", "captain": {"same_captain": True}, "shared_players": 6,
                "weaknesses": ["Injured/doubtful: Calafiori"],
                "recent_transfers": [{"gameweek": 8, "in": {"name": "Tavernier"}, "out": {"name": "Tzolis"}}],
                "transfer_prediction": {"likely_transfers_out": [{"name": "Calafiori"}],
                                        "likely_transfers_in": [{"name": "N.Jackson"}, {"name": "Konsa"}]}}],
    "strategy": ["You're 6pts behind Palash."],
}


def test_the_rivals_are_distilled_to_standings_transfers_and_likely_moves(flow):
    text = flow.summarize_rivals(RIVALS)
    assert "you are 5 with 468 points" in text and "#4 Cero Miedo XI (Palash) 474 pts, 6 behind" in text
    assert "in Tavernier / out Tzolis (GW8)" in text and "likely next: out Calafiori; in N.Jackson, Konsa" in text
    assert "same captain: yes" in text


@pytest.mark.parametrize("raw", [{"a": 1}, {"result": {"a": 1}}, '{"a": 1}', {"result": '{"a": 1}'}])
def test_a_tool_reply_unwraps_whatever_shape_the_hub_hands_over(flow, raw):
    assert flow.unwrap(raw) == {"a": 1}


ELEMENTS = [
    {"id": 1, "web_name": "Haaland", "now_cost": 157, "cost_change_start": 2},    # first squad: bought at 15.5, now 15.7
    {"id": 2, "web_name": "Groß", "now_cost": 62, "cost_change_start": 7},         # transferred in at 5.9, now 6.2
    {"id": 3, "web_name": "Faller", "now_cost": 55, "cost_change_start": -5},      # bought at 6.0, fell to 5.5
    {"id": 4, "web_name": "Flat", "now_cost": 40, "cost_change_start": 0},
]
TRANSFERS = [
    {"element_in": 2, "element_in_cost": 59, "time": "2026-10-23T16:00:00Z"},
    {"element_in": 3, "element_in_cost": 60, "time": "2026-10-23T16:00:00Z"},
    {"element_in": 3, "element_in_cost": 58, "time": "2026-10-23T17:00:00Z"},   # the latest purchase counts
]


def test_a_selling_price_is_the_purchase_plus_half_the_rise_rounded_down_or_the_price_if_it_fell(flow):
    rows = {r["name"]: r["sell"] for r in flow.selling_prices([1, 2, 3, 4], ELEMENTS, TRANSFERS)}
    assert rows == {"Haaland": 156,   # 155 + (157-155)//2
                    "Groß": 60,        # 59 + (62-59)//2 = 59 + 1
                    "Faller": 55,      # bought at 5.8 (latest), now 5.5: the current price
                    "Flat": 40}


def test_the_true_budget_is_the_sale_value_plus_the_bank_not_the_value_at_current_prices(flow):
    text = flow.summarize_selling(flow.selling_prices([1, 2, 3, 4], ELEMENTS, TRANSFERS), 2)
    assert "TRUE BUDGET 31.3m" in text            # 15.6 + 6.0 + 5.5 + 4.0 + 0.2 bank
    assert "worth 31.4m at current prices: do not use that" in text
    assert '"budget": 31.3' in text and "Haaland=15.6" in text and "Groß=6.0" in text


def test_only_private_classic_leagues_are_offered_with_the_rank_and_size(flow):
    entry = {"leagues": {"classic": [
        {"id": 314, "name": "Overall", "league_type": "s", "entry_rank": 3187782},
        {"id": 547594, "name": "Squad IITI", "league_type": "x", "entry_rank": 5},
        {"id": 1186690, "name": "Stay Humble", "league_type": "x", "entry_rank": 4},
    ]}}
    text = flow.summarize_leagues(entry, {547594: 9, 1186690: 13})
    assert "Squad IITI (id 547594, you are 5 of 9)" in text and "Stay Humble (id 1186690, you are 4 of 13)" in text
    assert "Overall" not in text
    assert "none" in flow.summarize_leagues({"leagues": {"classic": []}}, {})


def test_the_scope_check_names_what_is_wrong_so_the_step_does_not_spend_its_attempts_downstream(flow):
    good = {"team": "2452109", "league": "547594", "goal": "climb", "budget": 100.1, "chips": ["3xc"]}
    assert flow.scope_problems(good) == []
    assert flow.scope_problems({**good, "league": ""}) == []                       # no league is allowed
    assert "ONE numeric league id" in flow.scope_problems({**good, "league": "547594,1186690"})[0]
    assert any("budget" in p for p in flow.scope_problems({**good, "budget": "unknown"}))
    assert any("goal" in p for p in flow.scope_problems({**good, "goal": " "}))
    assert any("team" in p for p in flow.scope_problems({**good, "team": "abc"}))
