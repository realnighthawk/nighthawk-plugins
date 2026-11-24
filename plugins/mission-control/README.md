# Mission Control plugin

One plugin for Claude Code and oh-my-pi. It registers one MCP connection (`shared`, the tenant's hub), ships Agent Skills,
and adds long-term memory and the workstation browser through `mc`. The same directory carries both client manifests.

| Piece | What it does |
|---|---|
| `shared` MCP | The one connection to the platform's connections, as `<connection>__<tool>` tools. Locally it is the public `/mcp` with one OAuth sign-in; in a sandbox `MISSION_CONTROL_CONNECTIONS_URL` points it at the tenant's hub directly. Connections are added and signed in on the web app's Connections page, not here. |
| Skills | `services` and the portable Agent Skill `workspace`. Task skills live in the optional plugins `travel`, `fpl` and `goals`. |
| Memory | The workspace's memory server (Hindsight) through the router, in both clients, from `mc`: oh-my-pi uses its own `hindsight` backend; Claude Code, which has no memory slot, uses this plugin's `SessionStart` hook (recall into context) and `SessionEnd` hook (retain a compact slice, never tool output). Both run only under `mc`; a plain `claude` or `omp` has no memory from this plugin. |
| Rules | `rules/browser.md`, always applied: browser work uses oh-my-pi's built-in browser, which is attached to the person's workstation. There is no separate browser connection. |
| Command | `mc omp` / `mc claude` (set up once by `mc/install.sh`, which also installs websocat and this plugin in whichever client is present): signs in through the browser, attaches the workstation's browser for that session (omp's built-in browser; for Claude Code, which has no browser slot, the `browser` MCP, Playwright over the same tunnel), reports the session to Mission Control, and starts the client. |
| Agents | Claude Code only: `services-researcher` (read-only research across the connected services). |

## Install

Claude Code:

```bash
claude plugin marketplace add realnighthawk/nighthawk-plugins --scope user
claude plugin install mission-control@mission-control-plugins --scope user
```

Then open `/mcp` and authenticate `plugin:mission-control:shared`, and start with `mc claude` for the workstation browser and memory (`mc/install.sh` installs `mc`).

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
| `MISSION_CONTROL_DISABLE_HOOKS` | Any value turns both signals into no-ops. |

## Hooks

Claude Code's `hooks/hooks.json` runs `scripts/session-start.sh` (recall) and `scripts/session-end.sh` (retain). They read
`MC_MEMORY_URL`, `MC_MEMORY_TOKEN` and `MC_MEMORY_BANK` (default `claude-code`), which `mc claude` sets; without a token they do nothing.
`MISSION_CONTROL_DISABLE_HOOKS` turns them off. oh-my-pi has no hook: `mc omp` selects its `hindsight` backend instead.

If the `agent-brain` plugin is also enabled, turn its hooks off (`AGENT_BRAIN_DISABLE_HOOKS=1`) or uninstall it.

## Server prerequisites

The public router must publish the MCP OAuth discovery documents and the oh-my-pi public client metadata
at `https://api.nighthawklabs.org/oauth/mission-control-client.json`. Clerk must admit that client and grant `openid`,
`profile`, `email`, and `offline_access`. If Clerk requires pre-registration, explicitly allow the metadata
URL under **OAuth applications** in the Clerk dashboard; do not enable unrestricted dynamic registration.
The oh-my-pi callback listens on `http://127.0.0.1:3334/callback`.


## Remove

```bash
claude plugin uninstall mission-control@mission-control-plugins --scope user
omp plugin uninstall mission-control --scope user
```
