# Mission Control: oh-my-pi plugin

Connects oh-my-pi to the agent harness: two MCP servers, the memory skills, and the session hooks.

| Piece | What it does |
|---|---|
| `reactor` MCP | The tenant's connected ecosystem — life goals and tasks, finance, maps, trips, wardrobe, FPL, Notion — behind four entry tools (`search_tools`, `call_tool`, `search_skills`, `get_skill`). |
| `hippocampus` MCP | The harness's long-term memory (agent-brain): `memory_recall`, `memory_retain`, `memory_reflect`, `memory_forget`. |
| Skills | `reactor` and `hippocampus`, the same instructions the other clients get. |
| Hooks | Signal-only TypeScript hooks: `before_agent_start` tells the agent to recall (and to retain any slice the last session spooled); `session_shutdown` spools a compact slice of the session. The agent makes every MCP call itself — no key, no network call in the hooks. |

## Install

```
omp plugin marketplace add realnighthawk/nighthawk-plugins
omp plugin install mission-control@mission-control-plugins --scope user
```

Marketplace installs are read from the catalogue. For a platform sandbox, the hub and memory
addresses come from `MISSION_CONTROL_HUB_URL` and `MISSION_CONTROL_MEMORY_URL` and need no sign-in:
they are on the tenant's private network. The agent identity is `MISSION_CONTROL_AGENT_ID`, sent as
`X-Agent-ID`; outside a sandbox the defaults point at the public endpoints and need authentication.

The plugin is declarative: `plugin.json`, `.mcp.json`, `skills/` and `hooks/pre/`. `omp` expands
`${VAR}` and `${VAR:-default}` in `.mcp.json`, so the same file works in a sandbox and outside it.
