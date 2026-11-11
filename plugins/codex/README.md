# Nighthawk Memory — Codex

Long-term memory for the Codex CLI through the Hippocampus MCP, signed in with OAuth.

```sh
sh plugins/codex/install.sh        # config.toml entry + AGENTS.md instructions
codex mcp login hippocampus        # browser OAuth, no key stored
```

`http_headers = { "X-Agent-ID" = "codex" }` makes memory record Codex as the speaker. The server pins one bank per user, so `bank_id` is only a label. Codex has no session hook that reliably reaches the agent, so recall is an instruction in `AGENTS.md`.
