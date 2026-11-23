# Mission Control plugin

One plugin for Claude Code and oh-my-pi. It registers the tenant's MCP servers directly, ships three Agent Skills,
and adds long-term memory with recall and retain hooks. The same directory carries both client manifests.

| Piece | What it does |
|---|---|
| Service MCP servers | `finance`, `maps`, `life`, `retro`, `health`, `fpl`, `fpl_intelligence`, and `reddit`, each registered directly. In a sandbox the addresses and owner subject come from `MISSION_CONTROL_*` variables; there is no hub. |
| `hippocampus` MCP | The harness's long-term memory (agent-brain) at `https://api.nighthawklabs.org/memory/mcp`: `memory_recall`, `memory_retain`, `memory_reflect`, `memory_forget`. |
| Skills | `hippocampus`, `services`, and the portable Agent Skill `workspace`. Task skills live in the optional plugins `travel`, `fpl` and `goals`. |
| Hooks | Claude Code: `SessionStart` asks for recall and `SessionEnd` spools a slice. oh-my-pi: `before_agent_start` and `session_shutdown` do the same from `hooks/pre/memory.ts`. The agent makes every MCP call itself. |
| Rules | `rules/browser.md`, always applied: browser work uses oh-my-pi's built-in browser, which is attached to the person's workstation. There is no separate browser connection. |
| Command | `mc omp` (installed once from `mc/install.sh`, shown on the Workstation page): signs in through the browser, attaches the workstation's browser to omp for that session, and starts omp. |
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

OMP installs one `mission-control:shared` server at `https://api.nighthawklabs.org/mcp`.
Run `/mcp reauth mission-control:shared` once for all services. Existing OMP credentials for
the same URL carry over from a manually added `mission-control` entry, which can be removed.

Claude Code uses the direct server configuration referenced by `.claude-plugin/plugin.json`.
Managed sandboxes running the pinned plugin revision keep their private connections and must
retain that pin until their OMP provisioning supports the shared connection.

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

Local OMP's `hooks/pre/memory.ts` asks the agent to recall on the first turn through `mission-control:shared`.
It uses OMP's existing sign-in; the hook does not open a separate memory connection. It also hands any
queued slices to the agent for retention through that connection, removing a slice only after successful retention.

Managed OMP with `MISSION_CONTROL_MEMORY_URL` or `MISSION_CONTROL_MEMORY_KEY` set continues to warm
memory directly. OMP spools at most ten conversation slices at shutdown. Claude Code uses its own
`hooks/hooks.json` and `scripts/session-*.sh` to signal recall and spool slices.

Retention is also skill-driven: call `memory_retain` when the user states a durable decision, preference, correction or
personal fact, and `/mission-control:hippocampus:remember` retains on demand.

If the `agent-brain` plugin is also enabled, turn its hooks off (`AGENT_BRAIN_DISABLE_HOOKS=1`) or uninstall it — two
memory plugins recall and retain twice against the same memory.

## Server prerequisites

The public router must publish the MCP OAuth discovery documents and the oh-my-pi public client metadata
at `https://api.nighthawklabs.org/oauth/mission-control-client.json`. Clerk must admit that client and grant `openid`,
`profile`, `email`, and `offline_access`. If Clerk requires pre-registration, explicitly allow the metadata
URL under **OAuth applications** in the Clerk dashboard; do not enable unrestricted dynamic registration.
The oh-my-pi callback listens on `http://127.0.0.1:3334/callback`.

Do not add an `Authorization` header or `headersHelper` for the `hippocampus` server — either disables Claude Code's
OAuth fallback.

## Remove

```bash
claude plugin uninstall mission-control@mission-control-plugins --scope user
omp plugin uninstall mission-control --scope user
```
