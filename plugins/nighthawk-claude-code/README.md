# Nighthawk: Claude Code plugin

Connects Claude Code to the agent harness. Two MCP servers, one skill, four
commands, two subagents, and the memory hooks.

| Piece | What it does |
|---|---|
| `hippocampus` MCP | The tenant's connected ecosystem — life goals and tasks, finance, maps, trips, wardrobe, FPL, Notion — behind four entry tools (`search_tools`, `call_tool`, `search_skills`, `get_skill`). Fixed at `https://api.nighthawklabs.org/hub/mcp`, native MCP OAuth — no token to copy. |
| `memory` MCP | The harness's long-term memory (agent-brain): `memory_recall`, `memory_retain`, `memory_reflect`, `memory_forget`. Configured by environment variables; off when they are unset. |
| `hippocampus` skill | Tool-belt + memory layer instructions: search before guessing, exact schemas, the source table, memory-write rules. Loads automatically for personal-data and connected-service tasks. |
| Hooks | `SessionStart` recalls relevant memory into the session; `SessionEnd` retains what the session produced. |
| Commands | `/nighthawk:remember`, `/nighthawk:recall`, `/nighthawk:forget` (confirms first), `/nighthawk:tools`. |
| Agents | `hub-researcher` (read-only research across the hub), `memory-curator` (turns finished work into retained memory). |

## Install

```bash
claude plugin marketplace add realnighthawk/nighthawk-plugins --scope user
claude plugin install nighthawk@nighthawk-plugins --scope user
```

Then open `/mcp`, select `plugin:nighthawk:hippocampus`, and authenticate. The
hub's tools appear as `mcp__plugin_nighthawk_hippocampus__*`; the memory tools
as `mcp__plugin_nighthawk_memory__*`.

For SSH/headless sessions:

```bash
claude mcp login plugin:nighthawk:hippocampus --no-browser
```

(`claude -p` and Agent SDK runs cannot complete OAuth; authenticate once in an
interactive session first.)

## Memory configuration

The memory server and hooks read `NIGHTHAWK_*` from the environment (Claude
Code `env` settings or a shell profile) or from a `KEY=VALUE` file: the path in
`NIGHTHAWK_CONFIG`, else `~/.config/nighthawk/plugin.env`, else
`~/.config/agent-brain/plugin.env`. `AGENT_BRAIN_*` equivalents are accepted.

| Variable | Meaning |
|---|---|
| `NIGHTHAWK_MCP_URL` | Streamable-HTTP URL of the memory server, e.g. `https://agent-memory.nighthawklabs.org/mcp`. Required for memory. |
| `NIGHTHAWK_API_KEY` | Sent as `X-API-Key`. |
| `NIGHTHAWK_BANK` | Bank name; one bank per user so every harness shares memory. Required for the hooks. |
| `NIGHTHAWK_DISABLE_HOOKS` | Any value turns both hooks into no-ops. |
| `NIGHTHAWK_RECALL_LIMIT`, `NIGHTHAWK_RECALL_TIMEOUT`, `NIGHTHAWK_RETAIN_MIN_TURNS`, `NIGHTHAWK_RETAIN_MIN_CHARS` | Accepted through the shared `AGENT_BRAIN_*` names. |

Without `NIGHTHAWK_MCP_URL` and `NIGHTHAWK_BANK` the hooks do nothing and the
`memory` server stays disconnected; the hub, skill, commands, and
`hub-researcher` still work.

## Hooks

`scripts/run.sh` runs `agent-brain-hook` — the memory hook binary released from
this repo — downloading it from GitHub Releases (checksum verified) on first
use and caching it in the plugin data directory.

- **SessionStart** — `memory_recall` for facts about the project; injected as a
  `<agent-brain-memory>` block.
- **SessionEnd** — queues the new turns and drains them to `memory_retain` in a
  detached process; a failed send stays in the outbox and is retried by the
  next hook. Recalled blocks are stripped before retaining.

Failures are logged to `hook.log` in the plugin data directory
(`~/.cache/nighthawk` outside Claude Code) and never block a prompt.

If the `agent-brain` plugin is also enabled, turn its hooks off
(`AGENT_BRAIN_DISABLE_HOOKS=1`) or uninstall it — two memory plugins recall and
retain twice against the same bank.

## Server prerequisites

The harness router must serve the MCP OAuth discovery documents
(`/.well-known/oauth-protected-resource` and
`/.well-known/oauth-authorization-server`) and Clerk must have CIMD
(preferred) or DCR enabled for the OAuth application, with default scopes
`openid profile email offline_access`.

Do not add an `Authorization` header or `headersHelper` for the
`hippocampus` server — either disables Claude Code's OAuth fallback.

## Remove

```bash
claude plugin uninstall nighthawk@nighthawk-plugins --scope user
```

Uninstalling also removes the stored OAuth credentials for the endpoint.
