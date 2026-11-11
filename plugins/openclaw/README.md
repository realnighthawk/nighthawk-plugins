# Nighthawk Memory — OpenClaw plugin

OpenClaw plugin (`kind: "memory"`) for the Hippocampus memory MCP at `https://api.nighthawklabs.org/memory/mcp`. The endpoint is fixed in the code, as in the Claude Code plugin; there is no `url` setting. It talks to the server directly over HTTP; there is no helper binary.

| Hook | Does |
|---|---|
| `before_prompt_build` | `memory_recall` on the prompt; the result is prepended as a `<hippocampus-memory>` block. Fails open. |
| `agent_end` | `memory_retain` of the finished turn as `user:` / `assistant:` lines. |

## Identity

Every request carries `X-Agent-ID: openclaw` (config `agentId`), so memory records OpenClaw as the speaker. It is one fixed agent, not derived per session. The server pins one bank per user, so `bank` (default `nighthawk`) is only a label the tools require.

## Credential

A tenant MCP token, `<tenant>.<hmac>`, sent as `Authorization: Bearer`. Mint it from the router's `MCP_TOKEN_SECRET`, then set `NIGHTHAWK_MCP_TOKEN` in the gateway's environment. OpenClaw's plugin API has no OAuth flow for a plugin to use, so this plugin uses the static token. (The Cursor and Codex plugins sign in with OAuth.)

## Install

```bash
openclaw plugins install --link ./plugins/openclaw
```

Merge `templates/openclaw.jsonc` into `~/.openclaw/openclaw.json`, set `NIGHTHAWK_MCP_TOKEN`, restart the gateway.

## Tests

```bash
npm test      # node --experimental-strip-types, against a fake MCP server
```
