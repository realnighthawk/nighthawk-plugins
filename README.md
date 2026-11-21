<img src="assets/mission-control.svg" width="96" align="right" alt="Mission Control">

# Mission Control plugins

Public client plugins for [agent-brain](https://github.com/realnighthawk/agent-brain) and the Agent Harness.

| Client | Path | Sign-in |
|--------|------|---------|
| Claude Code | [plugins/mission-control/](plugins/mission-control/README.md) | OAuth, `claude plugin install mission-control@mission-control-plugins --scope user` |
| oh-my-pi | [plugins/mission-control/](plugins/mission-control/README.md) | None in a platform sandbox (private network); OAuth outside. `omp plugin install mission-control@mission-control-plugins --scope user` |
| Claude app | [plugins/claude-app/](plugins/claude-app/README.md) | OAuth (memory only) |
| ChatGPT | [plugins/chatgpt-memory/](plugins/chatgpt-memory/README.md) | OAuth (memory only) |

Every client gets Hippocampus (memory). The consolidated Mission Control plugin (Claude Code and oh-my-pi) also
registers the tenant's service servers directly — finance, maps, life, retro, health, FPL, FPL intelligence, Reddit and
the browser — and ships the five Agent Skills below. The hosted apps (Claude, ChatGPT) are memory-only. The
host sets `MISSION_CONTROL_AGENT_ID` (`claude-code` or `ohmypi`) for the consolidated plugin; the hosted apps send their
fixed ids (`claude-app`, `chatgpt`). Memory is one bank per agent, named by that header; no call names a bank.

## Skills

The plugin ships five portable Agent Skills, written to the Claude Agent Skills format. `plugins/mission-control/skills`
is the source; `packages/cookbook` stages those five into the npm tarball at pack time, so there is no second copy in
the repository.

| Skill | What it does |
|---|---|
| `fpl-gameweek-planner` | Plans a Fantasy Premier League gameweek: squad, transfers, XI, captain, chips, league overlay |
| `manage-goals` | Creates and changes goals, tasks, events, reminders and measurements in the Life engine |
| `browser` | Drives the real browser; the next best option when a tool is missing or the site needs a login |
| `travel-planner` | Plans a trip in TREK with maps research, itinerary checks, budget and packing |
| `view-builder` | Builds, revises, opens or removes Life Engine artifacts and views |

`@nighthawklabs/cookbook` publishes the same skills for agents without a plugin marketplace:

```bash
npx @nighthawklabs/cookbook                 # every skill into ~/.agents/skills
npx @nighthawklabs/cookbook --skills travel-planner,manage-goals
npx @nighthawklabs/cookbook --dry-run
npx @nighthawklabs/cookbook --uninstall
```

## Repository layout

```
plugins/mission-control/  the service-bearing plugin: both manifests, one .mcp.json, skills, hooks, commands, agents
plugins/<client>/         the memory-only client plugins
packages/cookbook/        npm wrapper: install.mjs, lint, tests; stages the five skills at pack time
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

The npm package has no committed skills: `packages/cookbook/bin/stage-skills.mjs` copies the five portable skills from
`plugins/mission-control/skills` into the tarball at `prepack` (and before `make check`).

## Tests

```bash
make check
```

That runs the sync check, the skills package's lint and pytest, and the Mission Control hook test.

## Related

- Hosted memory API: private `agent-brain` repo (deploy your own `memory-api`).
- Memory Explorer UI: `agent-web`.
