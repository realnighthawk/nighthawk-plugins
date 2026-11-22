#!/usr/bin/env python3
"""Lint every skill directory against the Agent Skills contract.

A skill is discovered by its name and description, then read as a filesystem: `SKILL.md`, one level of references, and
scripts the agent runs. The checks protect that contract: valid frontmatter, a description that says what and when, a
body under 500 lines, resolvable one-level references, compiling scripts, no harness-only mechanisms, and no secrets.

Semantic selection is not lintable; `tests/contracts/routing-cases.json` is the labelled corpus for that.
"""

import py_compile
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "skills"
NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
LINK = re.compile(r"\[[^\]]*\]\(([^)#\s]+)")
TEXT_SUFFIXES = {".md", ".py", ".json", ".txt", ".yaml", ".yml", ".sh", ".js", ".ts", ".html", ".css"}

# The platform reads exactly these two fields; anything else is a harness or another client's setting.
ALLOWED_FIELDS = {"name", "description"}
MAX_NAME = 64
MAX_DESCRIPTION = 1024
MAX_BODY_LINES = 500
MAX_BODY_CHARS = 20_000

USE_TRIGGER = re.compile(r"(?i)\buse (this|it|when|whenever|for)\b")

# A skill is portable: it names no runtime entry point, tool loader, prompt include, or hub.
HARNESS_ONLY = (
    "run_code", "skill_sdk", "tenant_worker", "discover_tools", "load_skills", "ask_user", "finish_task",
    "{baseDir}", "{{include", "nighthawk-skill", "reactor", "search_tools", "call_tool",
    "preload:", "always:",
)
# `tools:` is only harness frontmatter; a body may say "tools" in prose, so the line-start form is checked separately.
HARNESS_LINE = re.compile(r"(?m)^(?:preload|tools|always):")
# MCP tools are fully qualified `server:tool`; a slash is the old hub form.
MCP_SLASH = re.compile(
    r"`(?:life|trek|maps|fpl|fpl_intelligence|reddit|exa|finance)/[A-Za-z][A-Za-z0-9_.]*`"
)

SECRET_PATTERNS = [
    re.compile(r"(?i)\b(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]"),
    re.compile(r"\b(sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16})\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]


def _frontmatter(md: Path) -> tuple[dict[str, str], str] | None:
    text = md.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    parts = text.split("---", 2)
    if len(parts) != 3:
        return None
    fields = {}
    for line in parts[1].splitlines():
        if ":" in line and not line.lstrip().startswith("#"):
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    return fields, parts[2]


def _local_links(md: Path) -> list[str]:
    return [target for target in LINK.findall(md.read_text(encoding="utf-8"))
            if not re.match(r"(?:[a-z]+:|#)", target)]


def lint(skill: Path) -> list[str]:
    problems: list[str] = []
    md = skill / "SKILL.md"
    if not md.is_file():
        return [f"{skill.name}: no SKILL.md"]
    parsed = _frontmatter(md)
    if parsed is None:
        return [f"{skill.name}: SKILL.md has no frontmatter"]
    fields, body = parsed

    unknown = sorted(set(fields) - ALLOWED_FIELDS)
    if unknown:
        problems.append(f"{skill.name}: unknown frontmatter {unknown}; allowed: {sorted(ALLOWED_FIELDS)}")

    if fields.get("name") != skill.name or not NAME.match(skill.name):
        problems.append(f"{skill.name}: name must equal the directory name (lowercase, hyphenated), got {fields.get('name')!r}")
    if len(skill.name) > MAX_NAME:
        problems.append(f"{skill.name}: name is longer than {MAX_NAME} characters")
    if re.search(r"(?i)\b(anthropic|claude)\b", skill.name):
        problems.append(f"{skill.name}: name may not contain the reserved word 'anthropic' or 'claude'")

    description = fields.get("description", "")
    if not description:
        problems.append(f"{skill.name}: no description")
    elif len(description) > MAX_DESCRIPTION:
        problems.append(f"{skill.name}: description is {len(description)} chars; keep it under {MAX_DESCRIPTION}")
    elif re.search(r"<[^>]+>", description):
        problems.append(f"{skill.name}: description may not contain XML tags")
    elif not USE_TRIGGER.search(description):
        problems.append(f"{skill.name}: description must say when to use it (Use when/for/this ...)")

    lines = body.count("\n") + 1
    if lines > MAX_BODY_LINES:
        problems.append(f"{skill.name}: SKILL.md body is {lines} lines; keep it under {MAX_BODY_LINES} lines")
    if len(body) > MAX_BODY_CHARS:
        problems.append(f"{skill.name}: SKILL.md body is {len(body)} chars; keep it under {MAX_BODY_CHARS}")

    text = md.read_text(encoding="utf-8")
    if "\\" in body:
        problems.append(f"{skill.name}: use forward slashes in paths")
    if HARNESS_LINE.search(text):
        problems.append(f"{skill.name}: harness frontmatter fields (preload/tools/always) are not part of a portable skill")
    for word in HARNESS_ONLY:
        if word in text:
            problems.append(f"{skill.name}: SKILL.md mentions {word!r}, which is not portable")
    for match in MCP_SLASH.finditer(text):
        problems.append(f"{skill.name}: {match.group(0)} uses the old server/tool form; write `server:tool`")

    for target in _local_links(md):
        path = (skill / target).resolve()
        if skill.resolve() not in path.parents or not path.exists():
            problems.append(f"{skill.name}: link {target!r} is missing or outside the skill")
            continue
        if path.suffix == ".md":
            nested = _local_links(path)
            if nested:
                problems.append(f"{skill.name}: {target} links to {nested[0]!r}; references are one level deep")

    for script in [*(skill / "scripts").glob("*.py")]:
        try:
            py_compile.compile(str(script), doraise=True)
        except py_compile.PyCompileError as e:
            problems.append(f"{skill.name}: {script.name}: {e.msg}")
    for path in skill.rglob("*"):
        if path.is_file() and path.suffix in TEXT_SUFFIXES:
            text = path.read_text(encoding="utf-8", errors="ignore")
            for word in ("tenant_worker", "skill_sdk", "nighthawk-skill"):
                if word in text:
                    problems.append(f"{skill.name}: {path.relative_to(skill)} depends on {word!r}")
                    break
            for pattern in SECRET_PATTERNS:
                if pattern.search(text):
                    problems.append(f"{skill.name}: {path.relative_to(skill)} looks like it contains a secret")
                    break
    return problems


def main() -> int:
    problems: list[str] = []
    for skill in sorted(s for s in ROOT.iterdir() if s.is_dir()):
        problems += lint(skill)
    print("\n".join(problems) or "skills ok")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
