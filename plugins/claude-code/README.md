# Mission Control: Claude Code plugin

Connects Claude Code to the agent harness. Two MCP servers, one skill, four
commands, two subagents, and the memory hooks.

| Piece | What it does |
|---|---|
| `reactor` MCP | The tenant's connected ecosystem — life goals and tasks, finance, maps, trips, wardrobe, FPL, Notion — behind four entry tools (`search_tools`, `call_tool`, `search_skills`, `get_skill`). Fixed at `https://api.nighthawklabs.org/hub/mcp`, native MCP OAuth — no token to copy. |
| `hippocampus` MCP | The harness's long-term memory (agent-brain) at `https://api.nighthawklabs.org/memory/mcp`, through the router with the same native MCP OAuth as Reactor: `memory_recall`, `memory_retain`, `memory_reflect`, `memory_forget`. No API key in the client config. |
| `hippocampus` skill | Tool-belt + memory layer instructions: search before guessing, exact schemas, the source table, memory-write rules. Loads automatically for personal-data and connected-service tasks. |
| Hooks | Signal-only scripts: `SessionStart` tells the agent to recall (and to retain any slice the last session spooled); `SessionEnd` spools a compact slice of the session. The agent makes every MCP call itself over its OAuth connection — no key, no network call in the hooks. |
| Commands | `/mission-control:hippocampus:remember`, `/mission-control:hippocampus:recall`, `/mission-control:hippocampus:forget` (confirms first), `/mission-control:reactor:tools`. |
| Agents | `hub-researcher` (read-only research across the hub), `memory-curator` (turns finished work into retained memory). |

## Install

```bash
claude plugin marketplace add realnighthawk/nighthawk-plugins --scope user
claude plugin install mission-control@mission-control-plugins --scope user
```

Then open `/mcp` and authenticate both `plugin:mission-control:reactor` and
`plugin:mission-control:hippocampus` (one Clerk consent each, same account).
Reactor's tools appear as `mcp__plugin_mission-control_reactor__*`; the memory tools
as `mcp__plugin_mission-control_hippocampus__*`.

For SSH/headless sessions:

```bash
claude mcp login plugin:mission-control:hippocampus --no-browser
```

(`claude -p` and Agent SDK runs cannot complete OAuth; authenticate once in an
interactive session first.)

## Memory bank

The `hippocampus` MCP server needs no configuration — it authenticates through
the router with OAuth like Reactor. Memory is one bank per agent, named by a fixed header:

| Variable | Meaning |
|---|---|
| (fixed) `X-Agent-ID: claude-code` | Sent on every call. Memory is one bank per agent: this header names the bank, so Claude Code's memory is its own, as in the Hindsight paper. |
| `MISSION_CONTROL_DISABLE_HOOKS` | Any value turns both signals into no-ops. |

## Hooks

Both hooks are tiny shell scripts. They make no network call, hold no
credential, and download nothing — every MCP interaction is the agent's own,
over the OAuth connection Claude Code already holds.

- **SessionStart** injects `<hippocampus-memory>`: call `memory_recall` before
  answering the first request; if the previous session spooled a slice, first
  delegate each slice to the `memory-curator` subagent then
  delete the file.
- **SessionEnd** spools a compact slice of the finished session (user and
  assistant text only, tool output dropped, last 120 KB) to the plugin data
  directory. The next session's start signal is what retains it — `SessionEnd`
  itself runs after the model is gone and cannot call a tool. At most 10
  slices are kept.

Retention is also skill-driven during a session: the skill tells the agent to
call `memory_retain` when the user states a durable decision, preference,
correction, or personal fact, and `/mission-control:hippocampus:remember` retains on demand.

The spool is plain text on this machine, never uploaded; only the compacted
slice the subagent retains is sent to the memory server.

If the `agent-brain` plugin is also enabled, turn its hooks off
(`AGENT_BRAIN_DISABLE_HOOKS=1`) or uninstall it — two memory plugins recall and
retain twice against the same memory.

## Server prerequisites

The harness router must serve the MCP OAuth discovery documents
(`/.well-known/oauth-protected-resource` and
`/.well-known/oauth-authorization-server`) and Clerk must have CIMD
(preferred) or DCR enabled for the OAuth application, with default scopes
`openid profile email offline_access`.

Do not add an `Authorization` header or `headersHelper` for the `reactor` or
`hippocampus` servers — either disables Claude Code's OAuth fallback.

## Remove

```bash
claude plugin uninstall mission-control@mission-control-plugins --scope user
```

Uninstalling also removes the stored OAuth credentials for the endpoint.
