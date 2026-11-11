# nighthawk-plugins

Public client plugins for [agent-brain](https://github.com/realnighthawk/agent-brain) and the Agent Harness.

| Client | Path | Sign-in |
|--------|------|---------|
| Cursor | [plugins/cursor/](plugins/cursor/README.md) | OAuth |
| Codex | [plugins/codex/](plugins/codex/README.md) | OAuth (`codex mcp login hippocampus`) |
| OpenClaw | [plugins/openclaw/](plugins/openclaw/README.md) | Tenant bearer token (`NIGHTHAWK_MCP_TOKEN`) |
| Claude Code | [plugins/claude-code/](plugins/claude-code/README.md) | OAuth, `claude plugin install nighthawk@nighthawk-plugins --scope user` |

Each client sends its own `X-Agent-ID` (`cursor`, `codex`, `openclaw`, `claude-code`), so memory records who spoke. The server pins one bank per user; a client's `bank_id` is only a label.

## Shared code

The memory protocol is written once in `shared/` and rendered into the Cursor rule and skill and the Codex `AGENTS.md`:

```bash
python3 scripts/sync-shared.py          # regenerate
python3 scripts/sync-shared.py --check  # also verifies every client uses the same endpoint and its own X-Agent-ID
```

## Tests

```bash
cd plugins/openclaw && npm test
```

## Related

- Hosted memory API: private `agent-brain` repo (deploy your own `memory-api`).
- Memory Explorer UI: `agent-web`.
