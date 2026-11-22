"""The shipped skills are portable: name and description only, no harness or hub mechanism, one level of references,
runnable scripts, and fully qualified MCP tool names."""

import py_compile
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = sorted((ROOT / "skills").glob("*/SKILL.md"))
TEXT_SUFFIXES = {".md", ".py", ".json", ".txt", ".yaml", ".yml", ".sh", ".js", ".ts"}
HARNESS_ONLY = (
    "run_code", "skill_sdk", "tenant_worker", "discover_tools", "load_skills", "ask_user", "finish_task",
    "{baseDir}", "{{include", "nighthawk-skill", "reactor", "search_tools", "call_tool",
)
MCP_SLASH = re.compile(r"`(?:life|trek|maps|fpl|fpl_intelligence|reddit|exa|finance)/[A-Za-z][A-Za-z0-9_.]*`")


def parts(path: Path):
    text = path.read_text(encoding="utf-8")
    front, body = text.split("---", 2)[1:]
    fields = {k.strip(): v.strip() for k, v in (line.split(":", 1) for line in front.strip().splitlines() if ":" in line)}
    return fields, body


def test_the_shipped_set():
    assert {p.parent.name for p in SKILLS} == {
        "fpl-gameweek-planner", "manage-goals", "travel-planner", "view-builder", "workspace",
    }


def test_the_frontmatter_is_only_name_and_description():
    for path in SKILLS:
        fields, _ = parts(path)
        assert set(fields) == {"name", "description"}, path
        assert fields["name"] == path.parent.name
        assert 0 < len(fields["description"]) <= 1024
        assert re.search(r"(?i)\buse (this|when|whenever|for)\b", fields["description"]), path


def test_no_skill_file_names_a_runtime_or_a_hub():
    for path in SKILLS:
        for file in path.parent.rglob("*"):
            if file.is_file() and file.suffix in TEXT_SUFFIXES:
                text = file.read_text(encoding="utf-8", errors="ignore")
                for word in HARNESS_ONLY:
                    assert word not in text, (file.relative_to(ROOT), word)


def test_mcp_tools_are_fully_qualified():
    for path in SKILLS:
        text = path.read_text(encoding="utf-8")
        assert not MCP_SLASH.search(text), (path.parent.name, MCP_SLASH.search(text).group(0))


def test_references_are_one_level_and_exist():
    link = re.compile(r"\[[^\]]*\]\(([^)#\s]+)")
    for path in SKILLS:
        for target in link.findall(path.read_text(encoding="utf-8")):
            if re.match(r"[a-z]+:|#", target):
                continue
            ref = path.parent / target
            assert ref.is_file(), (path.parent.name, target)
            if ref.suffix == ".md":
                nested = [t for t in link.findall(ref.read_text(encoding="utf-8")) if not re.match(r"[a-z]+:|#", t)]
                assert not nested, (path.parent.name, target, nested)


def test_scripts_compile():
    for script in (ROOT / "skills").glob("*/scripts/*.py"):
        py_compile.compile(str(script), doraise=True)


def test_every_script_the_skill_tells_the_agent_to_run_exists():
    command = re.compile(r"python3 (scripts/[A-Za-z0-9_]+\.py)")
    for path in SKILLS:
        for target in command.findall(path.read_text(encoding="utf-8")):
            assert (path.parent / target).is_file(), (path.parent.name, target)
