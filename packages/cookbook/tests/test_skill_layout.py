"""The Agent Skills contract: two frontmatter fields, a selectable description, a short body, one level of references,
compiling scripts, no harness mechanisms and no secrets."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_lint_accepts_the_skills_as_they_are():
    out = subprocess.run([sys.executable, str(ROOT / "tools" / "lint.py")], capture_output=True, text=True)
    assert out.returncode == 0, out.stdout


@pytest.fixture
def broken(tmp_path, monkeypatch):
    sys.path.insert(0, str(ROOT / "tools"))
    import lint
    monkeypatch.setattr(lint, "ROOT", tmp_path)
    yield lint, tmp_path
    sys.path.remove(str(ROOT / "tools"))


def _skill(root, name, front="", files=None, body="body\n"):
    d = root / name
    d.mkdir()
    (d / "SKILL.md").write_text(f"---\nname: {name}\ndescription: Use when testing this skill.\n{front}---\n{body}")
    for rel, text in (files or {}).items():
        (d / rel).parent.mkdir(parents=True, exist_ok=True)
        (d / rel).write_text(text)
    return d


def test_a_well_formed_skill_passes(broken):
    lint, root = broken
    d = _skill(root, "demo", files={"scripts/x.py": "print(1)\n", "references/a.md": "text\n"}, body="See [a](references/a.md).\n")
    assert lint.lint(d) == []


@pytest.mark.parametrize("front", ["preload: life/tasks_list\n", "tools: life\n", "always: true\n", "engine: plan\n"])
def test_lint_rejects_fields_that_are_not_part_of_a_portable_skill(broken, front):
    lint, root = broken
    assert any("unknown frontmatter" in p for p in lint.lint(_skill(root, "demo", front)))


@pytest.mark.parametrize("name,expect", [("a" * 65, "longer than"), ("claude-helper", "reserved word"), ("Bad_Name", "directory name")])
def test_lint_rejects_a_name_the_platform_refuses(broken, name, expect):
    lint, root = broken
    assert any(expect in p for p in lint.lint(_skill(root, name)))


def test_lint_rejects_an_xml_tag_in_a_description(broken):
    lint, root = broken
    d = _skill(root, "demo")
    (d / "SKILL.md").write_text("---\nname: demo\ndescription: Use when <b>testing</b> this skill.\n---\nbody\n")
    assert any("XML tags" in p for p in lint.lint(d))


def test_lint_rejects_a_description_that_never_says_when(broken):
    lint, root = broken
    d = _skill(root, "demo")
    (d / "SKILL.md").write_text("---\nname: demo\ndescription: Handles goals.\n---\nbody\n")
    assert any("must say when to use it" in p for p in lint.lint(d))


def test_lint_rejects_a_description_over_the_limit(broken):
    lint, root = broken
    d = _skill(root, "demo")
    (d / "SKILL.md").write_text(f"---\nname: demo\ndescription: Use when {'x' * 1024}.\n---\nbody\n")
    assert any("description is" in p for p in lint.lint(d))


def test_lint_rejects_a_body_over_500_lines(broken):
    lint, root = broken
    d = _skill(root, "demo", body="line\n" * 501)
    assert any("500 lines" in p for p in lint.lint(d))


def test_lint_rejects_a_missing_reference(broken):
    lint, root = broken
    d = _skill(root, "demo", body="See [x](references/none.md).\n")
    assert any("missing or outside" in p for p in lint.lint(d))


def test_lint_rejects_a_nested_reference(broken):
    lint, root = broken
    d = _skill(root, "demo", files={"references/a.md": "See [b](b.md).\n", "references/b.md": "x\n"},
               body="See [a](references/a.md).\n")
    assert any("one level deep" in p for p in lint.lint(d))


def test_lint_rejects_the_old_server_slash_tool_form(broken):
    lint, root = broken
    d = _skill(root, "demo", body="Call `life/tasks_list`.\n")
    assert any("server/tool" in p for p in lint.lint(d))


def test_lint_rejects_a_harness_import_in_a_script(broken):
    lint, root = broken
    d = _skill(root, "demo", files={"scripts/x.py": "from tenant_worker.skill_sdk import call_tool\n"})
    assert any("tenant_worker" in p for p in lint.lint(d))


def test_lint_rejects_a_secret(broken):
    lint, root = broken
    d = _skill(root, "demo", files={"references/notes.md": "token = 'sk-" + "a" * 30 + "'\n"})
    assert any("contains a secret" in p for p in lint.lint(d))


def test_the_routing_corpus_covers_every_skill():
    data = json.loads((ROOT / "tests" / "contracts" / "routing-cases.json").read_text())
    cases = data["cases"]
    assert all(set(c) == {"request", "expect"} and c["request"].strip() for c in cases)
    routable = {path.parent.name for path in (ROOT / "skills").glob("*/SKILL.md")}
    expected = {c["expect"] for c in cases if c["expect"]}
    assert expected == routable, f"routing cases and skills differ: {sorted(expected ^ routable)}"
    assert any(c["expect"] is None for c in cases), "keep null cases so false positives are measured"
    requests = [c["request"] for c in cases]
    assert len(requests) == len(set(requests)), "duplicate routing request"
