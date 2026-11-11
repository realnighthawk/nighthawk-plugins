<img src="assets/mission-control.svg" width="96" align="right" alt="Mission Control">

# Mission Control plugins

Public client plugins for [agent-brain](https://github.com/realnighthawk/agent-brain) and the Agent Harness.

| Client | Path | Sign-in |
|--------|------|---------|
| Cursor | [plugins/cursor/](plugins/cursor/README.md) | OAuth |
| Codex | [plugins/codex/](plugins/codex/README.md) | OAuth (`codex mcp login hippocampus`, `codex mcp login reactor`) |
| OpenClaw | [plugins/openclaw/](plugins/openclaw/README.md) | Tenant bearer token (`MISSION_CONTROL_MCP_TOKEN`) |
| Claude Code | [plugins/claude-code/](plugins/claude-code/README.md) | OAuth, `claude plugin install mission-control@mission-control-plugins --scope user` |

Every client gets both servers, Hippocampus (memory) and Reactor (the tool hub), plus a skill for each. Each client sends its own `X-Agent-ID` (`cursor`, `codex`, `openclaw`, `claude-code`), so memory records who spoke. Memory is one bank per agent, named by that header; no call names a bank.

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
