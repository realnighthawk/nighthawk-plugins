# Agent Brain: Claude Code plugin

Connects Claude Code to the agent-brain memory server (the Python MCP server in the agent-brain repo,
`workers/temporal-worker/mcp_server.py`). The hooks are one small Go binary, `agent-brain-hook`, which `scripts/run.sh` downloads from the GitHub release (checksum verified) on first use and caches in the plugin data directory. Nothing else needs installing.

What it does:

| Hook | Action |
|---|---|
| `SessionStart` | Injects facts about the project (`memory_recall`). |
| `UserPromptSubmit` | Injects facts relevant to the prompt (`memory_recall`). |
| `Stop` | After each reply, queues the new turns for `memory_retain` once 6 turns or 4000 characters have built up. |
| `PreCompact`, `SessionEnd` | Queue whatever is new, however small. |

Retain extracts facts with a model, so it is not called per turn. Sending runs in a detached process, and
a payload that fails to send stays in `~/.cache/agent-brain/outbox/` and is retried by the next hook.
Recalled memory is wrapped in `<agent-brain-memory>` tags and stripped from the transcript before retaining,
so it is never written back as something the user said. Tool results and thinking are dropped; each tool call
becomes one line naming the tool and its target.

## Install

```bash
claude plugin marketplace add /path/to/agent-plugins --scope user
claude plugin install agent-brain@agent-plugins --scope user
```

Configure with environment variables (shell profile or Claude Code `env` settings) or a file at
`~/.config/agent-brain/plugin.env` with `KEY=VALUE` lines:

| Variable | Meaning |
|---|---|
| `AGENT_BRAIN_MCP_URL` | Streamable-HTTP URL of the server, for example `http://localhost:8890/mcp`. Required. |
| `AGENT_BRAIN_BANK` | Bank name. Use one bank per user so every harness shares memory. Required. |
| `AGENT_BRAIN_API_KEY` | Sent as `X-API-Key` when the server sets `RETAIN_MCP_API_KEY`. |
| `AGENT_BRAIN_RECALL_LIMIT`, `AGENT_BRAIN_RECALL_TIMEOUT` | Facts injected (default 8), seconds to wait (default 8). |
| `AGENT_BRAIN_RETAIN_MIN_TURNS`, `AGENT_BRAIN_RETAIN_MIN_CHARS` | Retain thresholds (default 6 turns or 4000 characters). |
| `AGENT_BRAIN_DISABLE_HOOKS` | Any value turns every hook into a no-op. |

Without `AGENT_BRAIN_MCP_URL` and `AGENT_BRAIN_BANK` the hooks do nothing. Failures are logged to
`~/.cache/agent-brain/hook.log` and never block a prompt. If the binary cannot be downloaded the hooks do nothing.

## Development

```bash
go test ./internal/abhook   # runs the hooks against an in-process MCP server
go build -o /tmp/agent-brain-hook ./cmd/agent-brain-hook
AGENT_BRAIN_HOOK_BIN=/tmp/agent-brain-hook claude   # use a local build
```

Releases: pushing a `v*` tag builds `agent-brain-hook-{darwin,linux}-{amd64,arm64}` plus `checksums.txt`. Set `AGENT_BRAIN_HOOK_VERSION` to pin a tag; the default is `latest`.
