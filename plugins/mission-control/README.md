# Mission Control plugin

One plugin for Claude Code and oh-my-pi. It registers the tenant's MCP servers directly, ships four Agent Skills,
and adds long-term memory with recall and retain hooks. The same directory carries both client manifests.

| Piece | What it does |
|---|---|
| Service MCP servers | `finance`, `maps`, `life`, `retro`, `health`, `fpl`, `fpl_intelligence`, `reddit` and `auto_browser`, each registered directly. In a sandbox the addresses, owner subject and browser bearer come from `MISSION_CONTROL_*` variables; there is no hub. |
| `hippocampus` MCP | The harness's long-term memory (agent-brain) at `https://api.nighthawklabs.org/memory/mcp`: `memory_recall`, `memory_retain`, `memory_reflect`, `memory_forget`. |
| Skills | `hippocampus`, `services`, and two portable Agent Skills: `browser`, `workspace`. Task skills live in the optional plugins `travel`, `fpl` and `goals`. |
| Hooks | Claude Code: `SessionStart` asks for recall and `SessionEnd` spools a slice. oh-my-pi: `before_agent_start` and `session_shutdown` do the same from `hooks/pre/memory.ts`. The agent makes every MCP call itself. |
| Rules | `rules/browser.md`, always applied: use the deployed `auto_browser` MCP for browser work, and try it when a tool is missing or a call fails. |
| Commands | Claude Code only: `/mission-control:hippocampus:remember`, `:recall`, `:forget` (confirms first). |
| Agents | Claude Code only: `services-researcher` (read-only research across the connected servers) and `memory-curator` (turns finished work into retained memory). |

## Install

Claude Code:

```bash
claude plugin marketplace add realnighthawk/nighthawk-plugins --scope user
claude plugin install mission-control@mission-control-plugins --scope user
```

Then open `/mcp` and authenticate `plugin:mission-control:hippocampus`. For SSH/headless sessions:

```bash
claude mcp login plugin:mission-control:hippocampus --no-browser
```

oh-my-pi:

```bash
omp plugin marketplace add realnighthawk/nighthawk-plugins
omp plugin install mission-control@mission-control-plugins --scope user
```

Marketplace installs are read from the catalogue. Inside a platform sandbox the service addresses and the memory
address come from `MISSION_CONTROL_<SERVICE>_URL` / `MISSION_CONTROL_MEMORY_URL` and need no sign-in; the agent identity
is `MISSION_CONTROL_AGENT_ID`. Outside a sandbox the memory endpoint needs OAuth and the host must still set
`MISSION_CONTROL_AGENT_ID` to `claude-code` or `ohmypi` so each harness keeps its own memory bank.

The plugin is declarative: `.claude-plugin/plugin.json` (Claude Code), `plugin.json` (oh-my-pi), `.mcp.json`, `skills/`,
`hooks/`, `commands/`, `agents/`. `omp` expands `${VAR}` and `${VAR:-default}` in `.mcp.json`, so the same file works in
a sandbox and outside it.

## Identity and memory

Memory is one bank per agent, named by `X-Agent-ID`. The consolidated plugin serves two harnesses, so the host supplies
the id:

| Variable | Meaning |
|---|---|
| `MISSION_CONTROL_AGENT_ID` | Sent as `X-Agent-ID`. Set it to `claude-code` or `ohmypi`; the sandbox host does this. |
| `MISSION_CONTROL_MEMORY_URL` | Memory endpoint; defaults to the public OAuth endpoint. |
| `MISSION_CONTROL_MEMORY_KEY` | Optional key for an in-network memory service; ignored when empty. |
| `MISSION_CONTROL_DISABLE_HOOKS` | Any value turns both signals into no-ops. |

## Hooks

Claude Code's hooks are `hooks/hooks.json` plus `scripts/session-*.sh`; oh-my-pi's is `hooks/pre/memory.ts`. Both are
signal-only: no network call, no credential, no download. Every MCP interaction is the agent's own.

- **Start** injects the memory instruction: call `memory_recall` before the first answer; if the previous session
  spooled a slice, delegate each slice to `memory-curator`, then delete the file.
- **End** spools a compact slice of the session (user and assistant text only, tool output dropped, last 120 KB) to the
  plugin data directory. The next start retires it. At most 10 slices are kept.

Retention is also skill-driven: call `memory_retain` when the user states a durable decision, preference, correction or
personal fact, and `/mission-control:hippocampus:remember` retains on demand.

If the `agent-brain` plugin is also enabled, turn its hooks off (`AGENT_BRAIN_DISABLE_HOOKS=1`) or uninstall it — two
memory plugins recall and retain twice against the same memory.

## Server prerequisites

The memory router must serve the MCP OAuth discovery documents
(`/.well-known/oauth-protected-resource` and `/.well-known/oauth-authorization-server`) and Clerk must have CIMD
(preferred) or DCR enabled, with default scopes `openid profile email offline_access`.

Do not add an `Authorization` header or `headersHelper` for the `hippocampus` server — either disables Claude Code's
OAuth fallback.

## Remove

```bash
claude plugin uninstall mission-control@mission-control-plugins --scope user
omp plugin uninstall mission-control --scope user
```
