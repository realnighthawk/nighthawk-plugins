# Agent skills

Eight portable Agent Skills, written to the [Claude Agent Skills format](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices).
Any agent that reads a `SKILL.md` can use them.

This is the npm package inside the [Mission Control plugin repository](https://github.com/realnighthawk/nighthawk-plugins).
The source is `plugins/mission-control/skills`; `bin/stage-skills.mjs` copies the portable skills into this package
at `prepack` (and before `make check`), so there is no second committed copy. The plugin install ships the same files;
the npm package is for agents without a plugin marketplace.

| Skill | What it does |
|---|---|
| `fpl-gameweek-planner` | Plans a Fantasy Premier League gameweek: squad, transfers, XI, captain, chips, league overlay |
| `manage-goals` | Creates and changes goals, tasks, events, reminders and measurements in the Life engine |
| `browser` | Drives the real browser; the next best option when a tool is missing or the site needs a login |
| `travel-planner` | Plans a trip in TREK with maps research, itinerary checks, budget and packing |
| `view-builder` | Builds, revises, opens or removes Life Engine artifacts and views |
| `project-init` | Plans and scaffolds a project, then creates the git repository |
| `project-ci` | Adds GitHub Actions checks for the project’s stacks |
| `project-cd` | Adds container and Helm release/deployment |

## Layout

```
skills/<skill-name>/
  SKILL.md            name and description in the frontmatter, then the procedure
  references/*.md     lookup material, read only when the skill points to it
  scripts/*.py        deterministic helpers, run with python3 scripts/<name>.py
  assets/*.md         templates the skill writes from
```

`SKILL.md` is the only required file. The body stays under 500 lines; detail goes in one level of `references/`, linked
directly from `SKILL.md`.

## Install

```bash
npx @nighthawklabs/cookbook                 # every skill into ~/.agents/skills
npx @nighthawklabs/cookbook --skills travel-planner,manage-goals
npx @nighthawklabs/cookbook --dry-run
npx @nighthawklabs/cookbook --list
npx @nighthawklabs/cookbook --uninstall     # remove only what this package installed
```

Or copy `skills/<name>/` into the skills directory your client reads. The installer copies the whole directory and
writes a marker; it touches nothing outside `~/.agents/skills`.

The skills call MCP servers by name — `life:`, `trek:`, `maps:`, `auto_browser:`, `fpl:`, `fpl_intelligence:`,
`reddit:`, `exa:`. Connect the servers you have; a skill that needs a missing server says so and stops rather than
inventing a result.

## Authoring

`.claude/skills/skill-authoring/SKILL.md` is the authoring procedure for this repository. It is developer tooling, not a
shipped skill.

`make check` is the executable contract:

```bash
python3 tools/lint.py      # frontmatter, description, 500-line body, one-level references, scripts, secrets
python3 -m pytest -q       # pure functions, CLI paths, installer, contracts
```

`tests/contracts/routing-cases.json` holds labelled requests for selection: one or more positives per skill plus null
cases. Update it when a description changes, and compare routers by top-1 accuracy and false positives, not by an
absolute score. `tests/contracts/life-operations.json` snapshots the Life engine's tool surface; refresh it with
`python3 tools/sync_life_contract.py` when the engine changes.

## Publishing

`.github/workflows/npm-publish.yml` at the repository root runs this package's `make check` on main and pull requests,
and publishes on a `cookbook-v*` tag. The tag must match `package.json`'s version.

```bash
git tag cookbook-v0.2.0
git push origin cookbook-v0.2.0
```

`NPM_TOKEN` must be an npm automation token with publish access to the `@nighthawklabs` scope.
