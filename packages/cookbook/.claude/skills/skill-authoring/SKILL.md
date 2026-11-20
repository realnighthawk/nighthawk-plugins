---
name: skill-authoring
description: Authors, changes, reviews or releases a skill in this repository (skills/<name>/). Use when adding or editing a SKILL.md, its references, scripts or assets, when its description changes, or when a skill fails lint, routing or a real task. Not for changing a client's MCP configuration.
---

# Authoring a skill

A skill is a directory the agent discovers and reads like a filesystem: `SKILL.md` first, then only the references it
needs, and scripts it runs with `python3`. It is a procedure, not an engine and not a workflow engine. Read the
[Agent Skills best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) before
editing.

**This file is developer tooling under `.claude/skills/`.** The npm package ships only `skills/`, so this procedure is
never installed or indexed. Do not move it under `skills/`.

## 0. Before writing

- Read the closest existing skill end to end.
- Read every description in `skills/*/SKILL.md`. If a broad word you plan to use is already a trigger for another skill,
  you are creating a collision.
- Build an evaluation first: run the task without the skill, note the specific failures, and write the cases into
  `tests/contracts/routing-cases.json`. Write only the instructions that fix those failures.
- Decide the freedom: high (judgement, heuristics), medium (a preferred pattern with parameters), or low (an exact
  script and command). Match it to how fragile the task is.

## 1. Frontmatter is the whole discovery surface

Exactly two fields. The platform preloads every skill's name and description into the system prompt; the body is read
only after selection.

| key | rule |
|---|---|
| `name` | required; equals the directory name; lowercase letters, numbers and hyphens; ≤64 chars; no `anthropic` or `claude` |
| `description` | required; ≤1,024 chars; one paragraph; no XML tags |

- **Write the description in the third person**: "Plans a trip", not "Plan a trip" or "I can plan a trip". It is injected
  into a system prompt, and a change of point of view is a discovery bug.
- Say **what it does and when to use it**, with the words a person would actually say: product names, verbs, ids, common
  paraphrases.
- Say what it is **not** for when a neighbouring skill could match ("Not for rendering arbitrary files ...").
- One job per skill. Do not stuff two procedures into one description to catch more requests.
- It is a trigger, not a tool list: do not claim capabilities in it.
- Changing a description changes selection. Update the routing cases and re-run the selection check.

## 2. The body

Keep `SKILL.md` **under 500 lines**; it competes with the conversation once loaded. Assume the model is already expert:
add only what it cannot infer.

- Numbered steps. Each step says what to do, what it leaves behind (a file, JSON, an id), and how it ends — a passing
  command or the next step.
- State the failure semantics: print every problem, exit non-zero, create nothing. No fallback path that reports success
  after doing nothing.
- Solve, do not defer. Catch the error the model would hit and say what to do with it; a bare `open()` or a tool error
  passed through unchanged is the model doing the script's job.
- For a multi-step write, validate the structured plan first, then apply it all-or-nothing; report every problem in one
  pass.
- A script that creates or changes something must be idempotent or print an `undo_key`; the model relays it.
- **No time-sensitive statements.** "As of this season", "not yet allowlisted", "version 2 is current" go stale. State
  the invariant and the check that yields the current value.
- One term per concept, used the same way everywhere.
- Concrete examples, not abstract descriptions.
- Justify every constant: a timeout, limit or threshold the model cannot derive is a bug. Put the reason beside the
  number.
- If the skill depends on a versioned external contract, snapshot the version and make a mismatch a visible stop.

## 3. Progressive disclosure

`SKILL.md` is the overview; detail lives in files the model reads only when needed.

- **One level deep.** Every reference file is linked directly from `SKILL.md`. A reference that links to another
  reference risks a partial read.
- Use forward slashes: `references/method.md`, never `references\method.md`.
- Name files for their content: `references/pitfalls.md`, not `references/doc2.md`.
- Keep a reference longer than 100 lines opening with a Contents list.
- Cite references as markdown links: `[references/method.md](references/method.md)`. Do not paste lookup material into
  the body.
- The repository's lint rejects a missing link and a nested one.

## 4. Scripts

`scripts/*.py` are runnable helpers, not a module the model imports. Say how to run them:

```bash
python3 scripts/plan.py check plan.json --tz Europe/Lisbon
```

- Run from the skill directory. Paths in commands are relative to it.
- Print one JSON object when the output is data; exit non-zero when the work could not be done, with every problem.
- Make the intent clear: "Run `scripts/x.py` to ..." (execute), not "see `scripts/x.py`" (read as reference).
- Keep the logic in pure functions and test them in `tests/`; the CLI is a thin wrapper.
- Handle the error the model would hit; do not punt it.
- List any required package in `SKILL.md`; do not assume it is installed.
- No voodoo constants: comment why the timeout, retry count or limit is that number.
- No network in tests. A non-trivial parser, money path or date path leaves one runnable check behind.

## 5. MCP tools

- Always use fully qualified names: `life:tasks_list`, `trek:list_trips`, `auto-browser:browser.observe`,
  `fantasy-pl:get_player_information`.
- Never guess a tool or an argument: name the server and tool, and let the client supply the schema.
- If a server is not connected, the skill says so and stops; it does not invent a result or fall back to a web guess.
- A skill may name another skill when that is the honest fallback (`signed-in-browser`, `view-builder`), but it does not
  assume the other skill is installed.

## 6. Verify

Run `make check` from the repository root.

```bash
python3 tools/lint.py      # frontmatter, description, body size, links, scripts, secrets
python3 -m pytest -q       # pure functions, CLI paths, installer, contracts
```

Selection is semantic and lint cannot judge it. `tests/contracts/routing-cases.json` is the labelled corpus: every skill
has a positive request, and null cases measure false positives. Re-measure with the real embedder where it is available,
and compare routers by top-1 accuracy and false positives.

Review checklist:

- [ ] `name` equals the directory; the description is third person, says what and when, and collides with no neighbour
- [ ] the body is under 500 lines and every step leaves a file, JSON or exit check
- [ ] failure prints every problem and exits non-zero; nothing pretends to have been created
- [ ] every link resolves inside the skill and references are one level deep
- [ ] scripts run from the skill directory, compile, and their logic is tested
- [ ] MCP tools are fully qualified `server:tool`; no hub, runtime or client-specific mechanism
- [ ] no secret, no absolute path, no time-sensitive claim without its check
- [ ] routing cases cover the skill; `make check` passes
