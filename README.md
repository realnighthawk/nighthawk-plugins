<img src="assets/mission-control.svg" width="96" align="right" alt="Mission Control">

# Mission Control plugins

Public client plugins for [agent-brain](https://github.com/realnighthawk/agent-brain) and the Agent Harness.

| Client | Path | Sign-in |
|--------|------|---------|
| Claude Code | [plugins/mission-control/](plugins/mission-control/README.md) | OAuth, `claude plugin install mission-control@mission-control-plugins --scope user` |
| oh-my-pi | [plugins/mission-control/](plugins/mission-control/README.md) | One OAuth sign-in for the public MCP; managed sandboxes use a pinned private setup |
| Claude app | [plugins/claude-app/](plugins/claude-app/README.md) | OAuth (memory only) |
| ChatGPT | [plugins/chatgpt-memory/](plugins/chatgpt-memory/README.md) | OAuth (memory only) |

Every client gets Hippocampus (memory). Mission Control also provides Finance, Maps, Life, Retro, Health,
FPL, FPL Intelligence and Reddit; the browser is omp's built-in one, attached to the person's workstation. OMP reaches them through one public MCP connection.
Claude Code and pinned managed sandboxes use direct connections. The hosted apps are memory-only.

## Skills

The plugins ship portable Agent Skills, written to the Claude Agent Skills format. `plugins/*/skills`
is the source; `packages/cookbook` stages those skills into the npm tarball at pack time, so there is no second copy in
the repository.

| Skill | What it does |
|---|---|
| `fpl-gameweek-planner` | Plans a Fantasy Premier League gameweek: squad, transfers, XI, captain, chips, league overlay |
| `manage-goals` | Creates and changes goals, tasks, events and reminders in the Life engine |
| `travel-planner` | Plans a trip in TREK with maps research, itinerary checks, budget and packing |
| `view-builder` | Builds, revises, opens or removes Life Engine artifacts: documents, decks, and trackers or lists backed by an app |
| `workspace` | Where projects live (`/workspace`), what persists, what the sandbox can reach, and how to report back |

The `travel` plugin registers [TREK MCP](https://trek.nighthawklabs.org/mcp) directly. After installing or updating
`travel@mission-control-plugins`, authorize TREK from `/mcp` in Claude Code or oh-my-pi. Maps and Life still come
from Mission Control. Managed sandboxes must allow HTTPS egress to `trek.nighthawklabs.org` for MCP and OAuth.

`@nighthawklabs/cookbook` publishes the same skills for agents without a plugin marketplace:

```bash
npx @nighthawklabs/cookbook                 # every skill into ~/.agents/skills
npx @nighthawklabs/cookbook --skills travel-planner,manage-goals
npx @nighthawklabs/cookbook --dry-run
npx @nighthawklabs/cookbook --uninstall
```

## Repository layout

```
plugins/mission-control/  Mission Control manifests, shared and direct MCP configs, skills, hooks, commands, agents
plugins/{travel,fpl,goals}/  optional skill plugins, installed per agent
plugins/<client>/         the memory-only client plugins
packages/cookbook/        npm wrapper: install.mjs, lint, tests; stages the skills at pack time
shared/                   the memory protocol, rendered into each client
scripts/sync-shared.py    regenerate the client memory text and verify identity/endpoints
```

## Generated files

The memory protocol is written once in `shared/` and rendered into each client's rule, `AGENTS.md` or skill. CI fails
when a generated tree is stale:

```bash
python3 scripts/sync-shared.py           # regenerate the memory text
python3 scripts/sync-shared.py --check
```

The npm package has no committed skills: `packages/cookbook/bin/stage-skills.mjs` copies the portable skills from
`plugins/*/skills` into the tarball at `prepack` (and before `make check`).

## Tests

```bash
make check
```

That runs the sync check, the skills package's lint and pytest, and the Mission Control hook test.

## Related

- Hosted memory API: private `agent-brain` repo (deploy your own `memory-api`).
- Memory Explorer UI: `agent-web`.
