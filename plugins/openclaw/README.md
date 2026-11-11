# Mission Control — OpenClaw plugin

OpenClaw plugin (`kind: "memory"`) for the Hippocampus memory MCP at `https://api.nighthawklabs.org/memory/mcp`, plus the Reactor hub at `https://api.nighthawklabs.org/hub/mcp` as a plain MCP server (`mcp.servers.reactor` in the template, same bearer token) and a skill for each (`skills/hippocampus`, `skills/reactor`, declared in the manifest). The endpoint is fixed in the code, as in the Claude Code plugin; there is no `url` setting. It talks to the server directly over HTTP; there is no helper binary.

| Hook | Does |
|---|---|
| `before_prompt_build` | `memory_recall` on the prompt; the result is prepended as a `<hippocampus-memory>` block. Fails open. |
| `agent_end` | `memory_retain` of the finished turn as `user:` / `assistant:` lines. |

## Identity

Every request carries `X-Agent-ID: openclaw` (config `agentId`), so memory records OpenClaw as the speaker. It is one fixed agent, not derived per session. Memory is one bank per agent, named by that header; no call names a bank.

## Credential

A tenant MCP token, `<tenant>.<hmac>`, sent as `Authorization: Bearer`. Mint it from the router's `MCP_TOKEN_SECRET`, then set `MISSION_CONTROL_MCP_TOKEN` in the gateway's environment. OpenClaw's plugin API has no OAuth flow for a plugin to use, so this plugin uses the static token. (The Cursor and Codex plugins sign in with OAuth.)

## Install

```bash
openclaw plugins install --link ./plugins/openclaw
```

Merge `templates/openclaw.jsonc` (it registers both the plugin and the `reactor` server) into `~/.openclaw/openclaw.json`, set `MISSION_CONTROL_MCP_TOKEN`, restart the gateway.

## Tests

```bash
npm test      # node --experimental-strip-types, against a fake MCP server
```
