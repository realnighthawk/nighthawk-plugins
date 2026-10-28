# Nighthawk: Claude Code plugin

Connects Claude Code to the agent harness. Two MCP servers, one skill, four
commands, two subagents, and the memory hooks.

| Piece | What it does |
|---|---|
| `reactor` MCP | The tenant's connected ecosystem — life goals and tasks, finance, maps, trips, wardrobe, FPL, Notion — behind four entry tools (`search_tools`, `call_tool`, `search_skills`, `get_skill`). Fixed at `https://api.nighthawklabs.org/hub/mcp`, native MCP OAuth — no token to copy. |
| `hippocampus` MCP | The harness's long-term memory (agent-brain) at `https://api.nighthawklabs.org/memory/mcp`, through the router with the same native MCP OAuth as Reactor: `memory_recall`, `memory_retain`, `memory_reflect`, `memory_forget`. No API key in the client config. |
| `hippocampus` skill | Tool-belt + memory layer instructions: search before guessing, exact schemas, the source table, memory-write rules. Loads automatically for personal-data and connected-service tasks. |
| Hooks | Two signal-only scripts: `SessionStart` tells the agent to recall, and a once-per-session `Stop` tells it to retain. The agent makes the MCP calls itself over its OAuth connection — no key, no network call in the hook. |
| Commands | `/nighthawk:remember`, `/nighthawk:recall`, `/nighthawk:forget` (confirms first), `/nighthawk:tools`. |
| Agents | `hub-researcher` (read-only research across the hub), `memory-curator` (turns finished work into retained memory). |

## Install

```bash
claude plugin marketplace add realnighthawk/nighthawk-plugins --scope user
claude plugin install nighthawk@nighthawk-plugins --scope user
```

Then open `/mcp` and authenticate both `plugin:nighthawk:reactor` and
`plugin:nighthawk:hippocampus` (one Clerk consent each, same account).
Reactor's tools appear as `mcp__plugin_nighthawk_reactor__*`; the memory tools
as `mcp__plugin_nighthawk_hippocampus__*`.

For SSH/headless sessions:

```bash
claude mcp login plugin:nighthawk:hippocampus --no-browser
```

(`claude -p` and Agent SDK runs cannot complete OAuth; authenticate once in an
interactive session first.)

## Memory bank

The `hippocampus` MCP server needs no configuration — it authenticates through
the router with OAuth like Reactor. The hooks read one optional setting to name
the bank in their instructions:

| Variable | Meaning |
|---|---|
| `NIGHTHAWK_BANK` (or `AGENT_BRAIN_BANK`) | Bank name; default `agent-harness`. One bank per user so every harness shares memory. |
| `NIGHTHAWK_DISABLE_HOOKS` | Any value turns both signals into no-ops. |

## Hooks

Both hooks are tiny shell scripts that only print an instruction. They make no
network call, hold no credential, and download nothing — the MCP interaction is
the agent's own, over the OAuth connection Claude Code already holds.

- **SessionStart** — injects `<hippocampus-memory>`: recall relevant facts with
  `memory_recall` before answering the first request, then use what is relevant.
- **Stop** — at most once per session, and only once the session is substantial
  (4+ user turns or 4 KB of transcript), blocks the final stop with a
  one-time instruction to retain durable decisions with `memory_retain`. If
  nothing is durable, the agent stops normally.

The skill also tells the agent to retain durable facts as they happen, so a
long session does not depend on the Stop signal alone.

If the `agent-brain` plugin is also enabled, turn its hooks off
(`AGENT_BRAIN_DISABLE_HOOKS=1`) or uninstall it — two memory plugins recall and
retain twice against the same bank.

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
claude plugin uninstall nighthawk@nighthawk-plugins --scope user
```

Uninstalling also removes the stored OAuth credentials for the endpoint.
