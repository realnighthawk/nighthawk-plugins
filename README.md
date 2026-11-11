# nighthawk-plugins

Public client plugins for [agent-brain](https://github.com/realnighthawk/agent-brain) (hosted MCP + hooks) and the Agent Harness.

| Client | Path | Sign-in |
|--------|------|---------|
| Cursor | [plugins/cursor/](plugins/cursor/README.md) | OAuth |
| Codex | [plugins/codex/](plugins/codex/README.md) | OAuth (`codex mcp login hippocampus`) |
| OpenClaw | [plugins/openclaw/](plugins/openclaw/README.md) | Tenant bearer token (`NIGHTHAWK_MCP_TOKEN`) |
| Claude Code (nighthawk) | [plugins/nighthawk-claude-code/](plugins/nighthawk-claude-code/README.md) | OAuth, `claude plugin install nighthawk@nighthawk-plugins --scope user` |
| Claude Code (memory, legacy) | [plugins/claude-code/](plugins/claude-code/README.md) | API key |

Each client sends its own `X-Agent-ID` (`cursor`, `codex`, `openclaw`, `claude-code`), so memory records who spoke. The server pins one bank per user; a client's `bank_id` is only a label.

## Tests

```bash
cd plugins/openclaw && npm test
plugins/claude-code/tests/run-hook-tests.sh
```

## Related

- Hosted memory API: private `agent-brain` repo (deploy your own `memory-api`).
- Memory Explorer UI: `agent-web`.
