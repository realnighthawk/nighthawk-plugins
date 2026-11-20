"""The browser skill against the browser's tool contract (tests/contracts/auto-browser-tools.json).

The skill tells the model to call `auto_browser:browser.*` tools, and to try the browser before reporting a missing
tool. A tool the controller does not serve is a step that cannot run. The order of the steps is the point of the skill
(a login is only kept if it is saved before the session closes), so that is held here too.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "browser"
CONTRACT = json.loads((ROOT / "tests" / "contracts" / "auto-browser-tools.json").read_text())
TOOLS = set(CONTRACT["tools"])
TOOL = re.compile(r"\bbrowser\.[a-z_]+\b")


def parts():
    text = (SKILL / "SKILL.md").read_text()
    front, body = text.split("---\n", 2)[1:]
    fields = dict(line.split(": ", 1) for line in front.strip().splitlines())
    return fields, body


def section(body, number):
    return re.search(rf"^## {number}\. .*?(?=^## |\Z)", body, re.S | re.M).group(0)


def test_every_tool_the_skill_names_is_one_the_controller_serves():
    texts = [(SKILL / "SKILL.md").read_text()] + [p.read_text() for p in (SKILL / "references").glob("*.md")]
    named = {m.group(0) for text in texts for m in TOOL.finditer(text)}
    assert named, "the skill names no browser tool"
    assert named <= TOOLS, sorted(named - TOOLS)


def test_every_browser_call_is_fully_qualified():
    _, body = parts()
    named = set(TOOL.findall(body))
    assert named
    for tool in named:
        assert f"auto_browser:{tool}" in body, tool


def test_the_steps_that_keep_a_login_are_there_and_in_order():
    _, body = parts()
    # a login is made in step 3 and kept by step 4, before the task and before any close
    assert body.index("## 3.") < body.index("## 4.") < body.index("## 5.")
    save = section(body, 4)
    assert "browser.save_auth_profile" in save and "browser.list_auth_profiles" in save
    assert re.search(r"before doing the task and before any close", save)
    finish = section(body, 5)
    assert finish.rindex("browser.save_auth_profile") < finish.rindex("browser.close_session"), "save, then close"
    # the session starts from the profile, and the sign-in itself is the person's
    assert "auth_profile" in section(body, 2)
    assert "browser.request_human_takeover" in section(body, 3)


def test_the_inputs_the_skill_relies_on_exist():
    inputs = CONTRACT["inputs"]
    _, body = parts()
    assert {"auth_profile", "start_url", "name"} <= set(inputs["browser.create_session"])
    assert {"session_id", "profile_name"} == set(inputs["browser.save_auth_profile"])
    assert "reason" in inputs["browser.request_human_takeover"]
    for field in ("auth_profile", "start_url", "profile_name", "reason"):
        assert f"`{field}`" in body or field in body, field


def test_the_skill_is_the_next_best_option_when_a_tool_is_missing():
    fields, body = parts()
    assert "missing" in fields["description"] and "fails" in fields["description"]
    assert "browser" in fields["description"]
    fallback = re.search(r"^## If a tool is missing.*?(?=^## |\Z)", body, re.S | re.M).group(0)
    assert "Before you tell the person a capability is missing" in fallback
    assert "tool call fails" in fallback
    assert "auto_browser" in fallback
    assert "JavaScript-only UI" in fallback
    assert "not a way around an approval" in fallback
    assert "engine that owns a record" in fallback


def test_the_omp_rule_wires_browser_work_to_auto_browser():
    rule = ROOT.parents[1] / "plugins" / "mission-control" / "rules" / "browser.md"
    text = rule.read_text()
    assert "alwaysApply: true" in text
    assert "auto_browser:browser.*" in text
    assert "oh-my-pi's built-in `browser` Eval prelude" in text
    assert "tool call fails" in text


def test_the_skill_never_asks_the_model_to_handle_a_credential():
    _, body = parts()
    assert "Never ask for, read or type a password" in body
    assert "browser.eval_js" in body and "cookies, tokens or storage" in body   # named only to forbid it


def test_an_agent_acts_only_on_sessions_it_created_so_several_agents_can_share_the_browser():
    _, body = parts()
    rules = body.split("## 1.")[0]
    assert "A session is yours only if you created it in this conversation" in rules
    assert "Never navigate in, take over, save a profile from, or close a session" in rules
    step1 = section(body, 1)
    assert "A session you did not create is open: leave it alone" in step1
    assert "Never close one that is not yours" in step1
    assert "reuse it" in step1 and "you created earlier in this conversation" in step1   # reuse is of its own session only
    assert "and only on it" in section(body, 5)
